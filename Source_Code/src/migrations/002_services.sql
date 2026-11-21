CREATE TABLE `bookmarks` (
	`user_id` text NOT NULL,
	`resource_id` text NOT NULL,
	`saved_at` text NOT NULL,
	PRIMARY KEY(`user_id`, `resource_id`),
	FOREIGN KEY (`user_id`) REFERENCES `app_users`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `notices` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`body` text NOT NULL,
	`status` text NOT NULL,
	`category_id` text,
	`expires_on` text DEFAULT '' NOT NULL,
	`updated_at` text NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `notices_by_status` ON `notices` (`status`,`updated_at`);--> statement-breakpoint
CREATE TABLE `recent_views` (
	`user_id` text NOT NULL,
	`resource_id` text NOT NULL,
	`viewed_at` text NOT NULL,
	PRIMARY KEY(`user_id`, `resource_id`),
	FOREIGN KEY (`user_id`) REFERENCES `app_users`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`resource_id`) REFERENCES `resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `recent_by_user` ON `recent_views` (`user_id`,`viewed_at`);--> statement-breakpoint
CREATE TABLE `usage_daily` (
	`day` text NOT NULL,
	`kind` text NOT NULL,
	`bucket` text NOT NULL,
	`total` integer DEFAULT 0 NOT NULL,
	PRIMARY KEY(`day`, `kind`, `bucket`)
);
