package com.softsmith.maker;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for creating a project
 */
public class CreateProjectRequest {

    @SerializedName("prompt")
    private String prompt;

    @SerializedName("name")
    private String name;

    @SerializedName("user_id")
    private String userId;

    public CreateProjectRequest(String prompt, String name, String userId) {
        this.prompt = prompt;
        this.name = name;
        this.userId = userId;
    }

    // Getters
    public String getPrompt() { return prompt; }
    public String getName() { return name; }
    public String getUserId() { return userId; }
}
