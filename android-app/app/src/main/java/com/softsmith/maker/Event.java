package com.softsmith.maker;

import com.google.gson.annotations.SerializedName;

/**
 * Event/log model
 */
public class Event {

    @SerializedName("id")
    private String id;

    @SerializedName("timestamp")
    private String timestamp;

    @SerializedName("level")
    private String level;

    @SerializedName("message")
    private String message;

    @SerializedName("source")
    private String source;

    public Event() {}

    // Getters
    public String getId() { return id; }
    public String getTimestamp() { return timestamp; }
    public String getLevel() { return level; }
    public String getMessage() { return message; }
    public String getSource() { return source; }
}
