-- ============================================================
-- OJ判题平台 - 数据库建表脚本
-- MySQL 5.7+ / 8.0+
-- 本地数据库密码: zjy200646
-- ============================================================

CREATE DATABASE IF NOT EXISTS oj_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE oj_platform;

-- ----------------------------
-- 用户表
-- ----------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role        ENUM('admin','student') NOT NULL DEFAULT 'student',
    nickname    VARCHAR(64)  DEFAULT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 默认管理员账号: admin / admin123
-- 【已修改】将这里的中文昵称改为了英文，避免 CMD 导入时因编码导致的乱码超长报错
INSERT INTO users (username, password, role, nickname) VALUES
  ('admin',  SHA2('admin123', 256), 'admin', 'SystemAdmin'),
  ('student1', SHA2('123456', 256), 'student', 'Student01'),
  ('student2', SHA2('123456', 256), 'student', 'Student02')
ON DUPLICATE KEY UPDATE username=username;

-- ----------------------------
-- 题目表
-- ----------------------------
CREATE TABLE IF NOT EXISTS problems (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT         NOT NULL,
    input_format    TEXT         DEFAULT NULL  COMMENT '输入格式说明',
    output_format   TEXT         DEFAULT NULL  COMMENT '输出格式说明',
    sample_input    TEXT         DEFAULT NULL  COMMENT '样例输入',
    sample_output   TEXT         DEFAULT NULL  COMMENT '样例输出',
    time_limit      INT          NOT NULL DEFAULT 1000  COMMENT '时间限制(ms)',
    memory_limit    INT          NOT NULL DEFAULT 65536 COMMENT '内存限制(KB)',
    created_by      INT          NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 判题数据（测试用例）表
-- ----------------------------
CREATE TABLE IF NOT EXISTS test_cases (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    problem_id      INT          NOT NULL,
    input_data      TEXT         NOT NULL,
    expected_output TEXT         NOT NULL,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 提交记录表
-- ----------------------------
CREATE TABLE IF NOT EXISTS submissions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    problem_id      INT          NOT NULL,
    user_id         INT          NOT NULL,
    code            LONGTEXT     NOT NULL,
    language        ENUM('c','cpp','java','python') NOT NULL DEFAULT 'cpp',
    status          ENUM(
                        'Pending','Compiling','Running',
                        'Accepted','Wrong Answer','Compile Error',
                        'Time Limit Exceeded','Memory Limit Exceeded',
                        'Runtime Error','System Error'
                    ) NOT NULL DEFAULT 'Pending',
    score           INT          NOT NULL DEFAULT 0    COMMENT '通过测试点数量/总测试点',
    test_total      INT          NOT NULL DEFAULT 0,
    compile_error   TEXT         DEFAULT NULL          COMMENT '编译错误信息',
    detail          JSON         DEFAULT NULL          COMMENT '各测试点详情',
    time_used       INT          DEFAULT NULL          COMMENT '运行时间(ms)',
    memory_used     INT          DEFAULT NULL          COMMENT '内存使用(KB)',
    submitted_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems(id),
    FOREIGN KEY (user_id)    REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- ============================================================
-- 第2部分：数据库高级特性（视图、存储过程、触发器）
-- ============================================================

-- ----------------------------
-- 视图1：学生成绩统计
-- ----------------------------
CREATE OR REPLACE VIEW v_student_progress AS
SELECT 
    u.id          AS user_id,
    u.username,
    u.nickname,
    COUNT(s.id)   AS total_submissions,
    SUM(CASE WHEN s.status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_count,
    COUNT(DISTINCT CASE WHEN s.status = 'Accepted' THEN s.problem_id END) AS problems_passed,
    CASE WHEN COUNT(s.id) > 0 
         THEN ROUND(SUM(CASE WHEN s.status = 'Accepted' THEN 1 ELSE 0 END) * 100.0 / COUNT(s.id), 1)
         ELSE 0 
    END AS pass_rate,
    MAX(s.submitted_at) AS last_submit_time
FROM users u
LEFT JOIN submissions s ON u.id = s.user_id
WHERE u.role = 'student'
GROUP BY u.id, u.username, u.nickname
ORDER BY problems_passed DESC, pass_rate DESC;

-- ----------------------------
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT 
    s.id            AS submission_id,
    p.title         AS problem_title,
    u.username      AS student_name,
    s.status,
    s.score,
    s.test_total,
    s.time_used,
    s.memory_used,
    s.submitted_at
FROM submissions s
JOIN problems p ON s.problem_id = p.id
JOIN users u ON s.user_id = u.id
ORDER BY s.submitted_at DESC
LIMIT 100;

-- ----------------------------
-- 存储过程1：学生排名（按通过率）
-- 参数: min_sub 最低提交次数门槛，默认1
-- ----------------------------
DELIMITER //
CREATE PROCEDURE sp_student_ranking(IN min_sub INT)
BEGIN
    IF min_sub IS NULL OR min_sub < 1 THEN
        SET min_sub = 1;
    END IF;
    
    SELECT 
        u.username,
        u.nickname,
        COUNT(s.id)   AS submissions,
        SUM(CASE WHEN s.status = 'Accepted' THEN 1 ELSE 0 END) AS passed,
        ROUND(SUM(CASE WHEN s.status = 'Accepted' THEN 1 ELSE 0 END) * 100.0 / COUNT(s.id), 1) AS rate,
        ROUND(AVG(CASE WHEN s.time_used IS NOT NULL THEN s.time_used END), 0) AS avg_time
    FROM users u
    JOIN submissions s ON u.id = s.user_id
    WHERE u.role = 'student'
    GROUP BY u.id, u.username, u.nickname
    HAVING COUNT(s.id) >= min_sub
    ORDER BY rate DESC, submissions DESC;
END //
DELIMITER ;

-- ----------------------------
-- 存储过程2：题目详细统计
-- 参数: pid 题目ID
-- ----------------------------
DELIMITER //
CREATE PROCEDURE sp_problem_detail(IN pid INT)
BEGIN
    -- 题目基本信息
    SELECT id, title, description, input_format, output_format,
           time_limit, memory_limit, created_at
    FROM problems WHERE id = pid;
    
    -- 提交统计
    SELECT 
        COUNT(*) AS total,
        SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted,
        SUM(CASE WHEN status = 'Wrong Answer' THEN 1 ELSE 0 END) AS wrong_answer,
        SUM(CASE WHEN status = 'Compile Error' THEN 1 ELSE 0 END) AS compile_error,
        SUM(CASE WHEN status = 'Time Limit Exceeded' THEN 1 ELSE 0 END) AS tle,
        SUM(CASE WHEN status = 'Runtime Error' THEN 1 ELSE 0 END) AS rte
    FROM submissions WHERE problem_id = pid;
    
    -- 最近提交
    SELECT s.id, u.username, s.status, s.score, s.time_used, s.submitted_at
    FROM submissions s
    JOIN users u ON s.user_id = u.id
    WHERE s.problem_id = pid
    ORDER BY s.submitted_at DESC
    LIMIT 10;
END //
DELIMITER ;

-- ----------------------------
-- 触发器1：插入用户时自动设置默认昵称
-- ----------------------------
DELIMITER //
CREATE TRIGGER trg_users_before_insert
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    IF NEW.nickname IS NULL OR NEW.nickname = '' THEN
        SET NEW.nickname = NEW.username;
    END IF;
END //
DELIMITER ;

-- ----------------------------
-- 触发器2：提交记录更新后记录变化日志
-- （在submissions表增加一个updated_at字段来追踪）
-- ----------------------------
ALTER TABLE submissions 
ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT NULL 
COMMENT '最后状态变更时间';

DELIMITER //
CREATE TRIGGER trg_submissions_before_update
BEFORE UPDATE ON submissions
FOR EACH ROW
BEGIN
    -- 当状态发生变化时，记录更新时间
    IF NEW.status != OLD.status OR OLD.status IS NULL THEN
        SET NEW.updated_at = NOW();
    END IF;
END //
DELIMITER ;
-- ----------------------------
-- 论坛帖子表
-- ----------------------------
CREATE TABLE IF NOT EXISTS forum_posts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    content     TEXT         NOT NULL,
    image_url   VARCHAR(512) DEFAULT NULL  COMMENT '图片链接',
    video_url   VARCHAR(512) DEFAULT NULL  COMMENT '视频链接',
    is_pinned   TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否置顶',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- ----------------------------
-- 比赛表
-- ----------------------------
CREATE TABLE IF NOT EXISTS contests (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT         DEFAULT NULL,
    start_time  DATETIME     NOT NULL,
    end_time    DATETIME     NOT NULL,
    created_by  INT          NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 比赛题目关联表（多对多）
-- ----------------------------
CREATE TABLE IF NOT EXISTS contest_problems (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    contest_id  INT NOT NULL,
    problem_id  INT NOT NULL,
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
    UNIQUE KEY uq_cp (contest_id, problem_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 比赛报名表（多对多）
-- ----------------------------
CREATE TABLE IF NOT EXISTS contest_registrations (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    contest_id     INT NOT NULL,
    user_id        INT NOT NULL,
    registered_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_cr (contest_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- 存储过程：ACM比赛排名
-- ----------------------------
DELIMITER //
CREATE PROCEDURE sp_contest_ranking(IN cid INT)
BEGIN
  SELECT 
    u.username,
    u.nickname,
    COUNT(DISTINCT CASE WHEN s.status = 'Accepted' THEN s.problem_id END) AS solved,
    COALESCE(
      SUM(CASE WHEN s.status = 'Accepted' AND s.first_ac = 1 
        THEN TIMESTAMPDIFF(SECOND, c.start_time, s.submitted_at) 
        ELSE 0 END), 0) AS penalty_seconds
  FROM contest_registrations cr
  JOIN users u ON cr.user_id = u.id
  JOIN contests c ON cr.contest_id = c.id
  LEFT JOIN (
    SELECT s.user_id, s.problem_id, s.status, s.submitted_at,
      CASE WHEN s.id = (
        SELECT MIN(s2.id) FROM submissions s2 
        WHERE s2.user_id = s.user_id AND s2.problem_id = s.problem_id 
          AND s2.status = 'Accepted' 
          AND s2.submitted_at BETWEEN c2.start_time AND c2.end_time
      ) THEN 1 ELSE 0 END AS first_ac
    FROM submissions s
    JOIN contest_problems cp ON s.problem_id = cp.problem_id
    JOIN contests c2 ON cp.contest_id = c2.id AND c2.id = cid
    WHERE s.submitted_at BETWEEN c2.start_time AND c2.end_time
  ) s ON cr.user_id = s.user_id
  WHERE cr.contest_id = cid
  GROUP BY u.id, u.username, u.nickname
  ORDER BY solved DESC, penalty_seconds ASC;
END //
DELIMITER ;
