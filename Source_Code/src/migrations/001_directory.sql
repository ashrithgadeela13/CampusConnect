CREATE TABLE `categories` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`icon` text NOT NULL,
	`color` text NOT NULL,
	`position` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `resources` (
	`id` text PRIMARY KEY NOT NULL,
	`category_id` text NOT NULL,
	`name` text NOT NULL,
	`summary` text NOT NULL,
	`description` text NOT NULL,
	`location` text NOT NULL,
	`hours` text NOT NULL,
	`email` text DEFAULT '' NOT NULL,
	`phone` text DEFAULT '' NOT NULL,
	`url` text NOT NULL,
	`tags` text DEFAULT '' NOT NULL,
	`next_steps` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'published' NOT NULL,
	`source_checked_on` text DEFAULT '' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	`updated_by` text NOT NULL,
	FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_resources_status_category` ON `resources` (`status`,`category_id`);--> statement-breakpoint
CREATE TABLE `app_settings` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `app_users` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`name` text NOT NULL,
	`role` text DEFAULT 'student' NOT NULL,
	`student_preview` integer DEFAULT 0 NOT NULL,
	`created_at` text NOT NULL
);
