package com.softsmith.maker;

import java.util.List;
import retrofit2.Call;
import retrofit2.http.*;

/**
 * Retrofit API service interface for Software Maker API
 */
public interface ApiService {

    @GET("projects")
    Call<List<Project>> getProjects(
        @Query("limit") int limit,
        @Query("offset") int offset
    );

    @GET("projects/{id}")
    Call<Project> getProject(@Path("id") String projectId);

    @POST("projects")
    Call<Project> createProject(@Body CreateProjectRequest request);

    @GET("projects/{id}/stats")
    Call<ProjectStats> getProjectStats(@Path("id") String projectId);

    @GET("projects/{id}/events")
    Call<List<Event>> getProjectEvents(
        @Path("id") String projectId,
        @Query("limit") int limit
    );

    @POST("projects/{id}/pause")
    Call<ApiResponse> pauseProject(@Path("id") String projectId);

    @POST("projects/{id}/resume")
    Call<ApiResponse> resumeProject(@Path("id") String projectId);

    @DELETE("projects/{id}")
    Call<ApiResponse> deleteProject(@Path("id") String projectId);
}
