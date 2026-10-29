-- 智慧宿舍人脸门禁与学生管理系统 数据库结构 (SQLite)
-- 由 SQLAlchemy 模型自动建库后导出，可直接用于建库

-- table: abnormal_event
CREATE TABLE abnormal_event (
	id INTEGER NOT NULL, 
	event_no VARCHAR(32) NOT NULL, 
	event_type VARCHAR(32) NOT NULL, 
	event_reason VARCHAR(128), 
	event_detail TEXT, 
	camera_id INTEGER, 
	camera_code VARCHAR(32), 
	student_id INTEGER, 
	student_no VARCHAR(32), 
	severity INTEGER, 
	status VARCHAR(16), 
	auto_feedback_sent BOOLEAN, 
	occurred_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(camera_id) REFERENCES camera_device (id), 
	FOREIGN KEY(student_id) REFERENCES student (id)
);

-- table: abnormal_handle
CREATE TABLE abnormal_handle (
	id INTEGER NOT NULL, 
	event_id INTEGER NOT NULL, 
	handler_id INTEGER, 
	handler_name VARCHAR(64), 
	handle_type VARCHAR(32), 
	handle_result VARCHAR(256), 
	handle_note TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(event_id) REFERENCES abnormal_event (id), 
	FOREIGN KEY(handler_id) REFERENCES sys_user (id)
);

-- table: access_point
CREATE TABLE access_point (
	id INTEGER NOT NULL, 
	code VARCHAR(32) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	building_id INTEGER, 
	camera_id INTEGER, 
	direction VARCHAR(8) NOT NULL, 
	status VARCHAR(16), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id), 
	FOREIGN KEY(camera_id) REFERENCES camera_device (id)
);

-- table: access_record
CREATE TABLE access_record (
	id INTEGER NOT NULL, 
	student_id INTEGER, 
	student_no VARCHAR(32), 
	student_name VARCHAR(64), 
	camera_id INTEGER NOT NULL, 
	camera_code VARCHAR(32), 
	building_id INTEGER, 
	building_name VARCHAR(64), 
	direction VARCHAR(8) NOT NULL, 
	similarity FLOAT, 
	verify_result VARCHAR(16) NOT NULL, 
	capture_image_path VARCHAR(256), 
	recognition_mode VARCHAR(32), 
	occurred_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, recognition_ms REAL DEFAULT 0.0, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(camera_id) REFERENCES camera_device (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id)
);

-- table: camera_device
CREATE TABLE camera_device (
	id INTEGER NOT NULL, 
	camera_code VARCHAR(32) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	location VARCHAR(256), 
	direction VARCHAR(8) NOT NULL, 
	building_id INTEGER, 
	stream_url VARCHAR(512), 
	device_status VARCHAR(16), 
	last_heartbeat DATETIME, 
	fps FLOAT, 
	recognition_success_rate FLOAT, 
	health_score FLOAT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id)
);

-- table: class_info
CREATE TABLE class_info (
	id INTEGER NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	grade_id INTEGER NOT NULL, 
	counselor_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(grade_id) REFERENCES grade (id), 
	FOREIGN KEY(counselor_id) REFERENCES sys_user (id)
);

-- table: college
CREATE TABLE college (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	code VARCHAR(32), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- table: dormitory_building
CREATE TABLE dormitory_building (
	id INTEGER NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	code VARCHAR(32), 
	floors INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

-- table: dormitory_room
CREATE TABLE dormitory_room (
	id INTEGER NOT NULL, 
	building_id INTEGER NOT NULL, 
	room_number VARCHAR(16) NOT NULL, 
	capacity INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id)
);

-- table: face_profile
CREATE TABLE face_profile (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	face_status VARCHAR(16) NOT NULL, 
	face_image_path VARCHAR(256), 
	face_embedding TEXT, 
	embedding_model VARCHAR(64), 
	face_quality_score FLOAT, 
	face_count INTEGER, 
	last_verify_time DATETIME, 
	verify_count INTEGER, 
	verify_success_count INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id), 
	FOREIGN KEY(student_id) REFERENCES student (id)
);

-- table: grade
CREATE TABLE grade (
	id INTEGER NOT NULL, 
	name VARCHAR(32) NOT NULL, 
	major_id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(major_id) REFERENCES major (id)
);

-- table: major
CREATE TABLE major (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	college_id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(college_id) REFERENCES college (id)
);

-- table: message_notification
CREATE TABLE message_notification (
	id INTEGER NOT NULL, 
	title VARCHAR(128) NOT NULL, 
	content TEXT, 
	message_type VARCHAR(32), 
	recipient_role VARCHAR(32), 
	recipient_id INTEGER, 
	recipient_class_id INTEGER, 
	related_event_id INTEGER, 
	is_read BOOLEAN, 
	read_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipient_class_id) REFERENCES class_info (id), 
	FOREIGN KEY(related_event_id) REFERENCES abnormal_event (id)
);

-- table: operation_log
CREATE TABLE operation_log (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(64), 
	action VARCHAR(128) NOT NULL, 
	target VARCHAR(256), 
	detail TEXT, 
	ip_address VARCHAR(64), 
	status INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES sys_user (id)
);

-- table: presence_status
CREATE TABLE presence_status (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	is_present BOOLEAN NOT NULL, 
	last_direction VARCHAR(8), 
	last_access_time DATETIME, 
	last_access_record_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(last_access_record_id) REFERENCES access_record (id)
);

-- table: student
CREATE TABLE student (
	id INTEGER NOT NULL, 
	student_no VARCHAR(32) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	gender VARCHAR(8), 
	phone VARCHAR(20), 
	id_card VARCHAR(32), 
	avatar_path VARCHAR(256), 
	info_complete INTEGER, 
	college_id INTEGER, 
	major_id INTEGER, 
	grade_id INTEGER, 
	class_id INTEGER, 
	building_id INTEGER, 
	room_id INTEGER, 
	user_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(college_id) REFERENCES college (id), 
	FOREIGN KEY(major_id) REFERENCES major (id), 
	FOREIGN KEY(grade_id) REFERENCES grade (id), 
	FOREIGN KEY(class_id) REFERENCES class_info (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id), 
	FOREIGN KEY(room_id) REFERENCES dormitory_room (id), 
	FOREIGN KEY(user_id) REFERENCES sys_user (id)
);

-- table: student_dormitory
CREATE TABLE student_dormitory (
	id INTEGER NOT NULL, 
	student_id INTEGER NOT NULL, 
	building_id INTEGER NOT NULL, 
	room_id INTEGER NOT NULL, 
	bed_no VARCHAR(16), 
	check_in_at DATETIME, 
	check_out_at DATETIME, 
	is_current BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(building_id) REFERENCES dormitory_building (id), 
	FOREIGN KEY(room_id) REFERENCES dormitory_room (id)
);

-- table: sys_log
CREATE TABLE sys_log (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(64), 
	action VARCHAR(128) NOT NULL, 
	target VARCHAR(256), 
	detail TEXT, 
	ip_address VARCHAR(64), 
	status INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES sys_user (id)
);

-- table: sys_permission
CREATE TABLE sys_permission (
	id INTEGER NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	module VARCHAR(64), 
	description VARCHAR(256), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

-- table: sys_role
CREATE TABLE sys_role (
	id INTEGER NOT NULL, 
	code VARCHAR(32) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	description VARCHAR(256), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

-- table: sys_user
CREATE TABLE sys_user (
	id INTEGER NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	real_name VARCHAR(64) NOT NULL, 
	phone VARCHAR(20), 
	email VARCHAR(128), 
	role VARCHAR(32) NOT NULL, 
	status INTEGER NOT NULL, 
	must_change_password BOOLEAN, 
	counselor_class_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(counselor_class_id) REFERENCES class_info (id)
);

-- table: sys_user_role
CREATE TABLE sys_user_role (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_role UNIQUE (user_id, role_id), 
	FOREIGN KEY(user_id) REFERENCES sys_user (id), 
	FOREIGN KEY(role_id) REFERENCES sys_role (id)
);

-- table: system_config
CREATE TABLE system_config (
	id INTEGER NOT NULL, 
	config_key VARCHAR(64) NOT NULL, 
	config_value VARCHAR(512), 
	description VARCHAR(256), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

-- index: ix_abnormal_event_event_no
CREATE UNIQUE INDEX ix_abnormal_event_event_no ON abnormal_event (event_no);

-- index: ix_abnormal_event_event_type
CREATE INDEX ix_abnormal_event_event_type ON abnormal_event (event_type);

-- index: ix_abnormal_event_occurred_at
CREATE INDEX ix_abnormal_event_occurred_at ON abnormal_event (occurred_at);

-- index: ix_abnormal_event_status
CREATE INDEX ix_abnormal_event_status ON abnormal_event (status);

-- index: ix_abnormal_status
CREATE INDEX ix_abnormal_status ON abnormal_event (status, event_type);

-- index: ix_access_point_code
CREATE UNIQUE INDEX ix_access_point_code ON access_point (code);

-- index: ix_access_point_direction
CREATE INDEX ix_access_point_direction ON access_point (direction);

-- index: ix_access_record_camera_id
CREATE INDEX ix_access_record_camera_id ON access_record (camera_id);

-- index: ix_access_record_direction
CREATE INDEX ix_access_record_direction ON access_record (direction);

-- index: ix_access_record_occurred
CREATE INDEX ix_access_record_occurred ON access_record (occurred_at DESC);

-- index: ix_access_record_occurred_at
CREATE INDEX ix_access_record_occurred_at ON access_record (occurred_at);

-- index: ix_access_record_student_id
CREATE INDEX ix_access_record_student_id ON access_record (student_id);

-- index: ix_access_record_verify_result
CREATE INDEX ix_access_record_verify_result ON access_record (verify_result);

-- index: ix_camera_device_camera_code
CREATE UNIQUE INDEX ix_camera_device_camera_code ON camera_device (camera_code);

-- index: ix_camera_device_device_status
CREATE INDEX ix_camera_device_device_status ON camera_device (device_status);

-- index: ix_camera_device_direction
CREATE INDEX ix_camera_device_direction ON camera_device (direction);

-- index: ix_face_profile_face_status
CREATE INDEX ix_face_profile_face_status ON face_profile (face_status);

-- index: ix_message_notification_message_type
CREATE INDEX ix_message_notification_message_type ON message_notification (message_type);

-- index: ix_message_notification_recipient_id
CREATE INDEX ix_message_notification_recipient_id ON message_notification (recipient_id);

-- index: ix_message_notification_recipient_role
CREATE INDEX ix_message_notification_recipient_role ON message_notification (recipient_role);

-- index: ix_presence_status_is_present
CREATE INDEX ix_presence_status_is_present ON presence_status (is_present);

-- index: ix_student_dormitory_is_current
CREATE INDEX ix_student_dormitory_is_current ON student_dormitory (is_current);

-- index: ix_student_dormitory_student_id
CREATE INDEX ix_student_dormitory_student_id ON student_dormitory (student_id);

-- index: ix_student_student_no
CREATE UNIQUE INDEX ix_student_student_no ON student (student_no);

-- index: ix_sys_permission_code
CREATE UNIQUE INDEX ix_sys_permission_code ON sys_permission (code);

-- index: ix_sys_role_code
CREATE UNIQUE INDEX ix_sys_role_code ON sys_role (code);

-- index: ix_sys_user_role
CREATE INDEX ix_sys_user_role ON sys_user (role);

-- index: ix_sys_user_role_role_id
CREATE INDEX ix_sys_user_role_role_id ON sys_user_role (role_id);

-- index: ix_sys_user_role_user_id
CREATE INDEX ix_sys_user_role_user_id ON sys_user_role (user_id);

-- index: ix_sys_user_username
CREATE UNIQUE INDEX ix_sys_user_username ON sys_user (username);

-- index: ix_system_config_config_key
CREATE UNIQUE INDEX ix_system_config_config_key ON system_config (config_key);
