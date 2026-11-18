-- =====================================================
-- CoworkingDB: збережені процедури для всіх сутностей
-- Запускати ПІСЛЯ coworking_db.sql (там уже є usp_Booking_Create / Cancel / Update)
-- CREATE OR ALTER -> скрипт можна запускати повторно
--
-- Коди помилок (THROW):
--   50001 користувача заблоковано        50002 користувач у чорному списку
--   50003 місце закрите для бронювання   50004 запис не знайдено
--   50010 email уже зайнятий             50011 недопустимий перехід статусу
--   50020 занадто часті листи (cooldown)
--   50012 є залежні записи (бронювання)  50013 оплата вже існує
-- =====================================================

/* =====================================================
   USERS
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_User_Register
    @Email        NVARCHAR(256),
    @PasswordHash VARCHAR(255),
    @Role         VARCHAR(20) = 'Client'
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF EXISTS (SELECT 1 FROM dbo.Users WHERE Email = @Email)
        THROW 50010, N'Користувач з таким email уже існує.', 1;

    BEGIN TRAN;
        INSERT dbo.Users (Email, Role) VALUES (@Email, @Role);
        DECLARE @Id INT = SCOPE_IDENTITY();
        INSERT dbo.UserAuth (UserId, PasswordHash) VALUES (@Id, @PasswordHash);
    COMMIT;

    SELECT Id, Email, Role, IsBlocked, IsEmailVerified, CreatedAt FROM dbo.Users WHERE Id = @Id;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_User_GetById @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, Email, Role, IsBlocked, IsEmailVerified, CreatedAt FROM dbo.Users WHERE Id = @UserId;
END;
GO

-- для логіну: повертає хеш і дані TOTP
CREATE OR ALTER PROCEDURE dbo.usp_User_GetForLogin @Email NVARCHAR(256)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.Id, u.Email, u.Role, u.IsBlocked, u.IsEmailVerified,
           a.PasswordHash, a.IsTotpEnabled, a.TotpSecret, a.LastTotpStep
    FROM dbo.Users u
    JOIN dbo.UserAuth a ON a.UserId = u.Id
    WHERE u.Email = @Email;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_User_List
    @Role VARCHAR(20) = NULL, @Search NVARCHAR(256) = NULL,
    @Offset INT = 0, @PageSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, Email, Role, IsBlocked, IsEmailVerified, CreatedAt
    FROM dbo.Users
    WHERE (@Role IS NULL OR Role = @Role)
      AND (@Search IS NULL OR Email LIKE N'%' + @Search + N'%')
    ORDER BY Id
    OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_User_SetRole @UserId INT, @Role VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Users SET Role = @Role WHERE Id = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_User_SetBlocked @UserId INT, @IsBlocked BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Users SET IsBlocked = @IsBlocked WHERE Id = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

-- Видалення користувача: лише якщо немає історії (бронювань, логів, менеджерства).
-- Інакше краще блокувати через usp_User_SetBlocked.
CREATE OR ALTER PROCEDURE dbo.usp_User_Delete @UserId INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF EXISTS (SELECT 1 FROM dbo.Booking     WHERE UserId = @UserId)
    OR EXISTS (SELECT 1 FROM dbo.AuditLog    WHERE UserId = @UserId)
    OR EXISTS (SELECT 1 FROM dbo.Coworking   WHERE ManagerId = @UserId)
    OR EXISTS (SELECT 1 FROM dbo.Blacklist   WHERE UserId = @UserId)
        THROW 50012, N'У користувача є історія (бронювання/логи/коворкінги). Заблокуйте його замість видалення.', 1;

    DELETE dbo.Users WHERE Id = @UserId;   -- UserAuth і RecoveryCode видаляться каскадно
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

/* =====================================================
   AUTH: пароль, Google Authenticator (TOTP), резервні коди
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_Auth_ChangePassword @UserId INT, @NewPasswordHash VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.UserAuth
    SET PasswordHash = @NewPasswordHash, PasswordChangedAt = SYSUTCDATETIME()
    WHERE UserId = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

-- 1) зберегти секрет (ще не активний) -> 2) після перевірки першого коду викликати Enable
CREATE OR ALTER PROCEDURE dbo.usp_Auth_SetTotpSecret @UserId INT, @TotpSecret VARBINARY(256)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.UserAuth
    SET TotpSecret = @TotpSecret, IsTotpEnabled = 0, TotpEnabledAt = NULL, LastTotpStep = NULL
    WHERE UserId = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Auth_EnableTotp @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.UserAuth
    SET IsTotpEnabled = 1, TotpEnabledAt = SYSUTCDATETIME()
    WHERE UserId = @UserId AND TotpSecret IS NOT NULL;
    IF @@ROWCOUNT = 0 THROW 50004, N'Секрет TOTP не задано.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Auth_DisableTotp @UserId INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRAN;
        UPDATE dbo.UserAuth
        SET IsTotpEnabled = 0, TotpSecret = NULL, TotpEnabledAt = NULL, LastTotpStep = NULL
        WHERE UserId = @UserId;
        DELETE dbo.UserRecoveryCode WHERE UserId = @UserId;
    COMMIT;
END;
GO

-- захист від повторного використання коду: повертає 1, якщо крок новий, і 0, якщо вже був
CREATE OR ALTER PROCEDURE dbo.usp_Auth_RegisterTotpStep @UserId INT, @Step BIGINT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.UserAuth SET LastTotpStep = @Step
    WHERE UserId = @UserId AND (LastTotpStep IS NULL OR LastTotpStep < @Step);
    SELECT CAST(CASE WHEN @@ROWCOUNT > 0 THEN 1 ELSE 0 END AS BIT) AS Accepted;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_RecoveryCode_Add @UserId INT, @CodeHash VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.UserRecoveryCode (UserId, CodeHash) VALUES (@UserId, @CodeHash);
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_RecoveryCode_Clear @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE dbo.UserRecoveryCode WHERE UserId = @UserId;
END;
GO

-- повертає 1, якщо код знайдено й погашено
CREATE OR ALTER PROCEDURE dbo.usp_RecoveryCode_Use @UserId INT, @CodeHash VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.UserRecoveryCode SET UsedAt = SYSUTCDATETIME()
    WHERE UserId = @UserId AND CodeHash = @CodeHash AND UsedAt IS NULL;
    SELECT CAST(CASE WHEN @@ROWCOUNT > 0 THEN 1 ELSE 0 END AS BIT) AS Accepted;
END;
GO

/* =====================================================
   AUDIT LOG
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_AuditLog_Add @UserId INT, @Action NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.AuditLog (UserId, Action) VALUES (@UserId, @Action);
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_AuditLog_List
    @UserId INT = NULL, @From DATETIME2(0) = NULL, @To DATETIME2(0) = NULL,
    @Offset INT = 0, @PageSize INT = 100
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, UserId, Action, CreatedAt
    FROM dbo.AuditLog
    WHERE (@UserId IS NULL OR UserId = @UserId)
      AND (@From   IS NULL OR CreatedAt >= @From)
      AND (@To     IS NULL OR CreatedAt <  @To)
    ORDER BY CreatedAt DESC, Id DESC
    OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY;
END;
GO

/* =====================================================
   COWORKING
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_Coworking_Create
    @Name NVARCHAR(150), @Address NVARCHAR(255),
    @Amenities NVARCHAR(500) = NULL, @ManagerId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.Coworking (Name, Address, Amenities, ManagerId)
    VALUES (@Name, @Address, @Amenities, @ManagerId);
    SELECT * FROM dbo.Coworking WHERE Id = SCOPE_IDENTITY();
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Coworking_Update
    @CoworkingId INT, @Name NVARCHAR(150), @Address NVARCHAR(255), @Amenities NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Coworking SET Name = @Name, Address = @Address, Amenities = @Amenities
    WHERE Id = @CoworkingId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Коворкінг не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Coworking_AssignManager @CoworkingId INT, @ManagerId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Coworking SET ManagerId = @ManagerId WHERE Id = @CoworkingId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Коворкінг не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Coworking_GetById @CoworkingId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM dbo.Coworking WHERE Id = @CoworkingId;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Coworking_List
    @Search NVARCHAR(150) = NULL, @ManagerId INT = NULL,
    @Offset INT = 0, @PageSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;
    SELECT c.Id, c.Name, c.Address, c.Amenities, c.ManagerId,
           (SELECT COUNT(*) FROM dbo.Workspace w WHERE w.CoworkingId = c.Id) AS WorkspaceCount
    FROM dbo.Coworking c
    WHERE (@ManagerId IS NULL OR c.ManagerId = @ManagerId)
      AND (@Search IS NULL OR c.Name LIKE N'%' + @Search + N'%' OR c.Address LIKE N'%' + @Search + N'%')
    ORDER BY c.Id
    OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY;
END;
GO

-- не дозволяємо видаляти, якщо в його місцях є бронювання
CREATE OR ALTER PROCEDURE dbo.usp_Coworking_Delete @CoworkingId INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF EXISTS (SELECT 1 FROM dbo.Booking b JOIN dbo.Workspace w ON w.Id = b.WorkspaceId
               WHERE w.CoworkingId = @CoworkingId)
        THROW 50012, N'У місцях коворкінгу є бронювання. Закрийте місця для бронювання замість видалення.', 1;

    DELETE dbo.Coworking WHERE Id = @CoworkingId;   -- Workspace і Blacklist видаляються каскадно
    IF @@ROWCOUNT = 0 THROW 50004, N'Коворкінг не знайдено.', 1;
END;
GO

/* =====================================================
   WORKSPACE
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_Workspace_Create
    @CoworkingId INT, @Type NVARCHAR(50), @PricePerHour DECIMAL(10,2), @IsOpenForBooking BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    INSERT dbo.Workspace (CoworkingId, Type, PricePerHour, IsOpenForBooking)
    VALUES (@CoworkingId, @Type, @PricePerHour, @IsOpenForBooking);
    SELECT * FROM dbo.Workspace WHERE Id = SCOPE_IDENTITY();
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Workspace_Update
    @WorkspaceId INT, @Type NVARCHAR(50), @PricePerHour DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Workspace SET Type = @Type, PricePerHour = @PricePerHour WHERE Id = @WorkspaceId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Робоче місце не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Workspace_SetOpen @WorkspaceId INT, @IsOpenForBooking BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Workspace SET IsOpenForBooking = @IsOpenForBooking WHERE Id = @WorkspaceId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Робоче місце не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Workspace_GetById @WorkspaceId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM dbo.Workspace WHERE Id = @WorkspaceId;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Workspace_ListByCoworking @CoworkingId INT, @OnlyOpen BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM dbo.Workspace
    WHERE CoworkingId = @CoworkingId AND (@OnlyOpen = 0 OR IsOpenForBooking = 1)
    ORDER BY Id;
END;
GO

-- вільні місця коворкінгу на інтервал
CREATE OR ALTER PROCEDURE dbo.usp_Workspace_FindAvailable
    @CoworkingId INT, @From DATETIME2(0), @To DATETIME2(0), @Type NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SELECT w.*
    FROM dbo.Workspace w
    WHERE w.CoworkingId = @CoworkingId
      AND w.IsOpenForBooking = 1
      AND (@Type IS NULL OR w.Type = @Type)
      AND NOT EXISTS (
          SELECT 1 FROM dbo.Booking b
          WHERE b.WorkspaceId = w.Id
            AND b.Status IN ('Pending','Confirmed')
            AND @From < b.EndTime AND b.StartTime < @To)
    ORDER BY w.PricePerHour;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Workspace_Delete @WorkspaceId INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM dbo.Booking WHERE WorkspaceId = @WorkspaceId)
        THROW 50012, N'У місця є бронювання. Закрийте його для бронювання замість видалення.', 1;
    DELETE dbo.Workspace WHERE Id = @WorkspaceId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Робоче місце не знайдено.', 1;
END;
GO

/* =====================================================
   BLACKLIST
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_Blacklist_Add
    @CoworkingId INT, @UserId INT, @Reason NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM dbo.Blacklist WHERE CoworkingId = @CoworkingId AND UserId = @UserId)
        UPDATE dbo.Blacklist SET Reason = @Reason
        WHERE CoworkingId = @CoworkingId AND UserId = @UserId;
    ELSE
        INSERT dbo.Blacklist (CoworkingId, UserId, Reason) VALUES (@CoworkingId, @UserId, @Reason);

    SELECT * FROM dbo.Blacklist WHERE CoworkingId = @CoworkingId AND UserId = @UserId;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Blacklist_Remove @CoworkingId INT, @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE dbo.Blacklist WHERE CoworkingId = @CoworkingId AND UserId = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Запису в чорному списку не знайдено.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Blacklist_ListByCoworking @CoworkingId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT bl.Id, bl.UserId, u.Email, bl.Reason
    FROM dbo.Blacklist bl
    JOIN dbo.Users u ON u.Id = bl.UserId
    WHERE bl.CoworkingId = @CoworkingId
    ORDER BY bl.Id;
END;
GO

/* =====================================================
   BOOKING (Create / Cancel / Update вже є в coworking_db.sql)
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_Booking_GetById @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT b.*, w.CoworkingId, w.PricePerHour
    FROM dbo.Booking b
    JOIN dbo.Workspace w ON w.Id = b.WorkspaceId
    WHERE b.Id = @BookingId;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Booking_ListByUser @UserId INT, @Status VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SELECT b.Id, b.WorkspaceId, w.Type AS WorkspaceType, c.Name AS CoworkingName,
           b.StartTime, b.EndTime, b.Status
    FROM dbo.Booking b
    JOIN dbo.Workspace w ON w.Id = b.WorkspaceId
    JOIN dbo.Coworking c ON c.Id = w.CoworkingId
    WHERE b.UserId = @UserId AND (@Status IS NULL OR b.Status = @Status)
    ORDER BY b.StartTime DESC;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Booking_ListByCoworking
    @CoworkingId INT, @From DATETIME2(0) = NULL, @To DATETIME2(0) = NULL, @Status VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SELECT b.Id, b.UserId, u.Email, b.WorkspaceId, w.Type AS WorkspaceType,
           b.StartTime, b.EndTime, b.Status
    FROM dbo.Booking b
    JOIN dbo.Workspace w ON w.Id = b.WorkspaceId
    JOIN dbo.Users u     ON u.Id = b.UserId
    WHERE w.CoworkingId = @CoworkingId
      AND (@From   IS NULL OR b.EndTime   > @From)
      AND (@To     IS NULL OR b.StartTime < @To)
      AND (@Status IS NULL OR b.Status = @Status)
    ORDER BY b.StartTime;
END;
GO

-- Pending -> Confirmed
CREATE OR ALTER PROCEDURE dbo.usp_Booking_Confirm @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Booking SET Status = 'Confirmed' WHERE Id = @BookingId AND Status = 'Pending';
    IF @@ROWCOUNT = 0 THROW 50011, N'Підтвердити можна лише бронювання у статусі Pending.', 1;
END;
GO

-- Confirmed -> Completed
CREATE OR ALTER PROCEDURE dbo.usp_Booking_Complete @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Booking SET Status = 'Completed' WHERE Id = @BookingId AND Status = 'Confirmed';
    IF @@ROWCOUNT = 0 THROW 50011, N'Завершити можна лише підтверджене бронювання.', 1;
END;
GO

/* =====================================================
   PAYMENT
   ===================================================== */
-- сума рахується автоматично: тривалість у годинах * ціна за годину
CREATE OR ALTER PROCEDURE dbo.usp_Payment_Create @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM dbo.Payment WHERE BookingId = @BookingId)
        THROW 50013, N'Оплата для цього бронювання вже існує.', 1;

    INSERT dbo.Payment (BookingId, Amount)
    SELECT b.Id,
           CAST(ROUND(DATEDIFF(MINUTE, b.StartTime, b.EndTime) / 60.0 * w.PricePerHour, 2) AS DECIMAL(10,2))
    FROM dbo.Booking b
    JOIN dbo.Workspace w ON w.Id = b.WorkspaceId
    WHERE b.Id = @BookingId AND b.Status IN ('Pending','Confirmed');

    IF @@ROWCOUNT = 0 THROW 50004, N'Бронювання не знайдено або вже неактивне.', 1;
    SELECT * FROM dbo.Payment WHERE BookingId = @BookingId;
END;
GO

-- успішна оплата + автоматичне підтвердження бронювання
CREATE OR ALTER PROCEDURE dbo.usp_Payment_Pay @BookingId INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRAN;
        UPDATE dbo.Payment SET Status = 'Paid', PaidAt = SYSUTCDATETIME()
        WHERE BookingId = @BookingId AND Status IN ('Pending','Failed');
        IF @@ROWCOUNT = 0 THROW 50011, N'Оплату не знайдено або вона вже проведена.', 1;

        UPDATE dbo.Booking SET Status = 'Confirmed'
        WHERE Id = @BookingId AND Status = 'Pending';
    COMMIT;

    SELECT * FROM dbo.Payment WHERE BookingId = @BookingId;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Payment_Fail @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Payment SET Status = 'Failed'
    WHERE BookingId = @BookingId AND Status = 'Pending';
    IF @@ROWCOUNT = 0 THROW 50011, N'Позначити невдалою можна лише оплату в статусі Pending.', 1;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Payment_Refund @BookingId INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    BEGIN TRAN;
        UPDATE dbo.Payment SET Status = 'Refunded'
        WHERE BookingId = @BookingId AND Status = 'Paid';
        IF @@ROWCOUNT = 0 THROW 50011, N'Повернути можна лише оплачений платіж.', 1;

        UPDATE dbo.Booking SET Status = 'Cancelled'
        WHERE Id = @BookingId AND Status IN ('Pending','Confirmed');
    COMMIT;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Payment_GetByBooking @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM dbo.Payment WHERE BookingId = @BookingId;
END;
GO

/* =====================================================
   EMAIL: підтвердження пошти і скидання пароля
   ===================================================== */
CREATE OR ALTER PROCEDURE dbo.usp_User_GetByEmail @Email NVARCHAR(256)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, Email, IsBlocked, IsEmailVerified FROM dbo.Users WHERE Email = @Email;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_User_MarkEmailVerified @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Users SET IsEmailVerified = 1 WHERE Id = @UserId;
    IF @@ROWCOUNT = 0 THROW 50004, N'Користувача не знайдено.', 1;
END;
GO

-- нова видача анулює попередні токени цього призначення; cooldown захищає від спаму листами
CREATE OR ALTER PROCEDURE dbo.usp_EmailToken_Create
    @UserId INT, @Purpose VARCHAR(20), @TokenHash CHAR(64),
    @ExpiresAt DATETIME2(0), @CooldownSeconds INT = 60
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF EXISTS (SELECT 1 FROM dbo.EmailToken
               WHERE UserId = @UserId AND Purpose = @Purpose
                 AND CreatedAt > DATEADD(SECOND, -@CooldownSeconds, SYSUTCDATETIME()))
        THROW 50020, N'Лист уже надіслано нещодавно. Спробуйте за хвилину.', 1;

    BEGIN TRAN;
        DELETE dbo.EmailToken WHERE UserId = @UserId AND Purpose = @Purpose;
        INSERT dbo.EmailToken (UserId, Purpose, TokenHash, ExpiresAt)
        VALUES (@UserId, @Purpose, @TokenHash, @ExpiresAt);
    COMMIT;
END;
GO

-- атомарно "гасить" токен і повертає UserId; порожній результат = токен недійсний/використаний/прострочений
CREATE OR ALTER PROCEDURE dbo.usp_EmailToken_Consume @TokenHash CHAR(64), @Purpose VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.EmailToken
    SET UsedAt = SYSUTCDATETIME()
    OUTPUT inserted.UserId
    WHERE TokenHash = @TokenHash AND Purpose = @Purpose
      AND UsedAt IS NULL AND ExpiresAt > SYSUTCDATETIME();
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_EmailToken_PurgeExpired
AS
BEGIN
    SET NOCOUNT ON;
    DELETE dbo.EmailToken
    WHERE ExpiresAt < DATEADD(DAY, -1, SYSUTCDATETIME())
       OR UsedAt    < DATEADD(DAY, -1, SYSUTCDATETIME());
END;
GO
