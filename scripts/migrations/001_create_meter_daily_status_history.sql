IF OBJECT_ID('MeterDailyStatusHistory', 'U') IS NULL
BEGIN
    CREATE TABLE MeterDailyStatusHistory (
        IdMeter INT NOT NULL,
        SnapshotDate DATE NOT NULL,
        ReferenceDateTime DATETIME NOT NULL,
        Status VARCHAR(10) NOT NULL,
        Reason NVARCHAR(200) NOT NULL,
        ReadingCount INT NOT NULL,
        BadIntervals INT NOT NULL,
        DownFrom DATETIME NULL,
        DownTo DATETIME NULL,
        CreatedAt DATETIME NOT NULL CONSTRAINT DF_MeterDailyStatusHistory_CreatedAt DEFAULT GETDATE(),
        UpdatedAt DATETIME NOT NULL CONSTRAINT DF_MeterDailyStatusHistory_UpdatedAt DEFAULT GETDATE(),
        CONSTRAINT PK_MeterDailyStatusHistory PRIMARY KEY (IdMeter, SnapshotDate)
    );

    CREATE INDEX IX_MeterDailyStatusHistory_SnapshotDate_Status
        ON MeterDailyStatusHistory (SnapshotDate, Status);

    CREATE INDEX IX_MeterDailyStatusHistory_Status
        ON MeterDailyStatusHistory (Status);
END
GO
