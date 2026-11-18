-- Підтвердження email і скидання пароля. Скрипт ідемпотентний (безпечно запускати повторно).

IF COL_LENGTH(N'dbo.Users', N'IsEmailVerified') IS NULL
BEGIN
    ALTER TABLE dbo.Users ADD IsEmailVerified BIT NOT NULL
        CONSTRAINT DF_Users_IsEmailVerified DEFAULT 0;
    -- уже існуючі користувачі вважаються підтвердженими (динамічно: колонка щойно з'явилась)
    EXEC (N'UPDATE dbo.Users SET IsEmailVerified = 1');
END
GO

IF OBJECT_ID(N'dbo.EmailToken', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.EmailToken (
        Id         INT IDENTITY(1,1) CONSTRAINT PK_EmailToken PRIMARY KEY,
        UserId     INT          NOT NULL,
        Purpose    VARCHAR(20)  NOT NULL,
        TokenHash  CHAR(64)     NOT NULL CONSTRAINT UQ_EmailToken_Hash UNIQUE,  -- SHA-256, сам токен не зберігаємо
        ExpiresAt  DATETIME2(0) NOT NULL,
        UsedAt     DATETIME2(0) NULL,
        CreatedAt  DATETIME2(0) NOT NULL CONSTRAINT DF_EmailToken_CreatedAt DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_EmailToken_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(Id) ON DELETE CASCADE,
        CONSTRAINT CK_EmailToken_Purpose CHECK (Purpose IN ('VerifyEmail','ResetPassword'))
    );
    CREATE INDEX IX_EmailToken_User_Purpose ON dbo.EmailToken(UserId, Purpose);
END
GO
