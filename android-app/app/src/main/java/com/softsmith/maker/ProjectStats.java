package com.softsmith.maker;

import com.google.gson.annotations.SerializedName;

/**
 * Project statistics model
 */
public class ProjectStats {

    @SerializedName("total_tasks")
    private int totalTasks;

    @SerializedName("pending_tasks")
    private int pendingTasks;

    @SerializedName("running_tasks")
    private int runningTasks;

    @SerializedName("completed_tasks")
    private int completedTasks;

    @SerializedName("failed_tasks")
    private int failedTasks;

    @SerializedName("progress_percentage")
    private float progressPercentage;

    public ProjectStats() {}

    // Getters
    public int getTotalTasks() { return totalTasks; }
    public int getPendingTasks() { return pendingTasks; }
    public int getRunningTasks() { return runningTasks; }
    public int getCompletedTasks() { return completedTasks; }
    public int getFailedTasks() { return failedTasks; }
    public float getProgressPercentage() { return progressPercentage; }
}
