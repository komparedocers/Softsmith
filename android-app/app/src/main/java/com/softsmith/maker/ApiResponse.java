package com.softsmith.maker;

import com.google.gson.annotations.SerializedName;

/**
 * Generic API response
 */
public class ApiResponse {

    @SerializedName("message")
    private String message;

    @SerializedName("success")
    private boolean success;

    public ApiResponse() {}

    // Getters
    public String getMessage() { return message; }
    public boolean isSuccess() { return success; }

    // Setters
    public void setMessage(String message) { this.message = message; }
    public void setSuccess(boolean success) { this.success = success; }
}
