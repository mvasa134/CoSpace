-- =====================================================
-- CoworkingDB (MS SQL Server / Azure SQL) — за UML-діаграмою
-- База має бути вже створена; скрипт виконується всередині неї (без CREATE DATABASE / USE)
-- Автентифікація (hash / Google Auth) винесена в UserAuth
-- =====================================================

-- ---------- Users ----------
CREATE TABLE dbo.Users (
    Id         INT IDENTITY(1,1) CONSTRAINT PK_Users PRIMARY KEY,
    Email      NVARCHAR(256) NOT NULL CONSTRAINT UQ_Users_Email UNIQUE,
    Role       VARCHAR(20)   NOT NULL CONSTRAINT DF_Users_Role DEFAULT 'Client',
    IsBlocked  BIT           NOT NULL CONSTRAINT DF_Users_IsBlocked DEFAULT 0,
    CreatedAt  DATETIME2(0)  NOT NULL CONSTRAINT DF_Users_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT CK_Users_Role CHECK (Role IN ('Client','SpaceManager','PlatformAdmin'))
);

-- ---------- UserAuth (окремо: хеш пароля + Google Authenticator / TOTP) ----------
CREATE TABLE dbo.UserAuth (
    UserId          INT            NOT NULL CONSTRAINT PK_UserAuth PRIMARY KEY,  -- 1:1 з Users
    PasswordHash    VARCHAR(255)   NOT NULL,        -- bcrypt / argon2, ніколи не пароль у відкритому вигляді
    TotpSecret      VARBINARY(256) NULL,            -- секрет для Google Authenticator (шифрувати на рівні застосунку)
    IsTotpEnabled   BIT            NOT NULL CONSTRAINT DF_UserAuth_TotpOn DEFAULT 0,
    TotpEnabledAt   DATETIME2(0)   NULL,
    LastTotpStep    BIGINT         NULL,            -- останній використаний 30-с інтервал (захист від повторного використання коду)
    PasswordChangedAt DATETIME2(0) NOT NULL CONSTRAINT DF_UserAuth_PwdChanged DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_UserAuth_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(Id) ON DELETE CASCADE,
    CONSTRAINT CK_UserAuth_Totp CHECK (IsTotpEnabled = 0 OR TotpSecret IS NOT NULL)
);

-- ---------- Резервні коди (на випадок втрати телефону з Authenticator) ----------
CREATE TABLE dbo.UserRecoveryCode (
    Id        INT IDENTITY(1,1) CONSTRAINT PK_UserRecoveryCode PRIMARY KEY,
    UserId    INT          NOT NULL,
    CodeHash  VARCHAR(255) NOT NULL,                -- зберігаємо лише хеш коду
    UsedAt    DATETIME2(0) NULL,
    CONSTRAINT FK_UserRecoveryCode_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(Id) ON DELETE CASCADE
);
CREATE INDEX IX_UserRecoveryCode_UserId ON dbo.UserRecoveryCode(UserId);

-- ---------- AuditLog ----------
CREATE TABLE dbo.AuditLog (
    Id         INT IDENTITY(1,1) CONSTRAINT PK_AuditLog PRIMARY KEY,
    UserId     INT           NOT NULL,
    Action     NVARCHAR(255) NOT NULL,
    CreatedAt  DATETIME2(0)  NOT NULL CONSTRAINT DF_AuditLog_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_AuditLog_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(Id)
);
CREATE INDEX IX_AuditLog_UserId ON dbo.AuditLog(UserId);

-- ---------- Coworking ----------
CREATE TABLE dbo.Coworking (
    Id         INT IDENTITY(1,1) CONSTRAINT PK_Coworking PRIMARY KEY,
    ManagerId  INT           NULL,                  -- User "керує" Coworking (0..1)
    Name       NVARCHAR(150) NOT NULL,
    Address    NVARCHAR(255) NOT NULL,
    Amenities  NVARCHAR(500) NULL,
    CONSTRAINT FK_Coworking_Manager FOREIGN KEY (ManagerId) REFERENCES dbo.Users(Id)
);
CREATE INDEX IX_Coworking_ManagerId ON dbo.Coworking(ManagerId);

-- ---------- Workspace (композиція: видалили коворкінг -> видалились місця) ----------
CREATE TABLE dbo.Workspace (
    Id               INT IDENTITY(1,1) CONSTRAINT PK_Workspace PRIMARY KEY,
    CoworkingId      INT           NOT NULL,
    Type             NVARCHAR(50)  NOT NULL,
    PricePerHour     DECIMAL(10,2) NOT NULL,
    IsOpenForBooking BIT           NOT NULL CONSTRAINT DF_Workspace_Open DEFAULT 1,
    CONSTRAINT FK_Workspace_Coworking FOREIGN KEY (CoworkingId)
        REFERENCES dbo.Coworking(Id) ON DELETE CASCADE,
    CONSTRAINT CK_Workspace_Price CHECK (PricePerHour >= 0)
);
CREATE INDEX IX_Workspace_CoworkingId ON dbo.Workspace(CoworkingId);

-- ---------- Blacklist ----------
CREATE TABLE dbo.Blacklist (
    Id          INT IDENTITY(1,1) CONSTRAINT PK_Blacklist PRIMARY KEY,
    CoworkingId INT           NOT NULL,             -- Coworking "веде"
    UserId      INT           NOT NULL,             -- User "потрапляє"
    Reason      NVARCHAR(500) NULL,
    CONSTRAINT FK_Blacklist_Coworking FOREIGN KEY (CoworkingId)
        REFERENCES dbo.Coworking(Id) ON DELETE CASCADE,
    CONSTRAINT FK_Blacklist_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(Id),
    CONSTRAINT UQ_Blacklist_CoworkingUser UNIQUE (CoworkingId, UserId)
);

-- ---------- Booking ----------
CREATE TABLE dbo.Booking (
    Id          INT IDENTITY(1,1) CONSTRAINT PK_Booking PRIMARY KEY,
    UserId      INT          NOT NULL,              -- User "створює"
    WorkspaceId INT          NOT NULL,              -- Workspace "бронюється"
    StartTime   DATETIME2(0) NOT NULL,
    EndTime     DATETIME2(0) NOT NULL,
    Status      VARCHAR(20)  NOT NULL CONSTRAINT DF_Booking_Status DEFAULT 'Pending',
    CONSTRAINT FK_Booking_Users     FOREIGN KEY (UserId)      REFERENCES dbo.Users(Id),
    CONSTRAINT FK_Booking_Workspace FOREIGN KEY (WorkspaceId) REFERENCES dbo.Workspace(Id),
    CONSTRAINT CK_Booking_Time   CHECK (EndTime > StartTime),
    CONSTRAINT CK_Booking_Status CHECK (Status IN ('Pending','Confirmed','Completed','Cancelled'))
);
CREATE INDEX IX_Booking_UserId ON dbo.Booking(UserId);
CREATE INDEX IX_Booking_Workspace_Time ON dbo.Booking(WorkspaceId, StartTime, EndTime);

-- ---------- Payment (1 бронювання -> 0..1 оплата, композиція) ----------
CREATE TABLE dbo.Payment (
    Id        INT IDENTITY(1,1) CONSTRAINT PK_Payment PRIMARY KEY,
    BookingId INT           NOT NULL CONSTRAINT UQ_Payment_Booking UNIQUE,
    Amount    DECIMAL(10,2) NOT NULL,
    Status    VARCHAR(20)   NOT NULL CONSTRAINT DF_Payment_Status DEFAULT 'Pending',
    PaidAt    DATETIME2(0)  NULL,
    CONSTRAINT FK_Payment_Booking FOREIGN KEY (BookingId)
        REFERENCES dbo.Booking(Id) ON DELETE CASCADE,
    CONSTRAINT CK_Payment_Amount CHECK (Amount >= 0),
    CONSTRAINT CK_Payment_Status CHECK (Status IN ('Pending','Paid','Failed','Refunded'))
);
GO

-- ---------- Заборона перетину броней одного місця ----------
CREATE TRIGGER dbo.TR_Booking_NoOverlap ON dbo.Booking
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN dbo.Booking b
          ON b.WorkspaceId = i.WorkspaceId
         AND b.Id <> i.Id
         AND b.Status IN ('Pending','Confirmed')
         AND i.Status IN ('Pending','Confirmed')
         AND i.StartTime < b.EndTime
         AND b.StartTime < i.EndTime
    )
    BEGIN
        RAISERROR(N'Це робоче місце вже заброньоване на цей час.', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO

-- ---------- Методи Booking: create / cancel / update ----------
CREATE PROCEDURE dbo.usp_Booking_Create
    @UserId INT, @WorkspaceId INT, @StartTime DATETIME2(0), @EndTime DATETIME2(0)
AS
BEGIN
    SET NOCOUNT ON;
    IF (SELECT IsBlocked FROM dbo.Users WHERE Id = @UserId) = 1
        THROW 50001, N'Користувача заблоковано.', 1;
    IF EXISTS (SELECT 1 FROM dbo.Blacklist bl
               JOIN dbo.Workspace w ON w.CoworkingId = bl.CoworkingId
               WHERE bl.UserId = @UserId AND w.Id = @WorkspaceId)
        THROW 50002, N'Користувач у чорному списку цього коворкінгу.', 1;
    IF (SELECT IsOpenForBooking FROM dbo.Workspace WHERE Id = @WorkspaceId) = 0
        THROW 50003, N'Місце закрите для бронювання.', 1;

    INSERT dbo.Booking (UserId, WorkspaceId, StartTime, EndTime)
    VALUES (@UserId, @WorkspaceId, @StartTime, @EndTime);

    SELECT * FROM dbo.Booking WHERE Id = SCOPE_IDENTITY();
END;
GO

CREATE PROCEDURE dbo.usp_Booking_Cancel @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Booking SET Status = 'Cancelled'
    WHERE Id = @BookingId AND Status IN ('Pending','Confirmed');
END;
GO

CREATE PROCEDURE dbo.usp_Booking_Update
    @BookingId INT, @StartTime DATETIME2(0), @EndTime DATETIME2(0)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Booking SET StartTime = @StartTime, EndTime = @EndTime
    WHERE Id = @BookingId AND Status IN ('Pending','Confirmed');
END;
GO
