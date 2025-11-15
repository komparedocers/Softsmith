package com.softsmith.maker;

import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Activity showing project details and logs
 */
public class ProjectDetailActivity extends AppCompatActivity {

    private TextView projectNameText;
    private TextView statusText;
    private TextView progressText;
    private ProgressBar progressBar;
    private RecyclerView eventsRecyclerView;
    private EventAdapter eventAdapter;

    private String projectId;
    private String projectName;
    private Handler refreshHandler;
    private Runnable refreshRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_project_detail);

        projectId = getIntent().getStringExtra("project_id");
        projectName = getIntent().getStringExtra("project_name");

        if (projectId == null) {
            Toast.makeText(this, "Invalid project ID", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        initViews();
        setupRecyclerView();
        loadProjectData();
        startAutoRefresh();
    }

    private void initViews() {
        projectNameText = findViewById(R.id.projectNameText);
        statusText = findViewById(R.id.statusText);
        progressText = findViewById(R.id.progressText);
        progressBar = findViewById(R.id.detailProgressBar);
        eventsRecyclerView = findViewById(R.id.eventsRecyclerView);

        projectNameText.setText(projectName != null ? projectName : "Project");
        setTitle("Project Details");
    }

    private void setupRecyclerView() {
        eventAdapter = new EventAdapter(new ArrayList<>());
        eventsRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        eventsRecyclerView.setAdapter(eventAdapter);
    }

    private void loadProjectData() {
        progressBar.setVisibility(View.VISIBLE);

        // Load project info
        ApiClient.getApiService().getProject(projectId).enqueue(new Callback<Project>() {
            @Override
            public void onResponse(Call<Project> call, Response<Project> response) {
                if (response.isSuccessful() && response.body() != null) {
                    updateProjectInfo(response.body());
                }
            }

            @Override
            public void onFailure(Call<Project> call, Throwable t) {
                Toast.makeText(ProjectDetailActivity.this,
                        "Error loading project", Toast.LENGTH_SHORT).show();
            }
        });

        // Load events
        ApiClient.getApiService().getProjectEvents(projectId, 50)
                .enqueue(new Callback<List<Event>>() {
            @Override
            public void onResponse(Call<List<Event>> call, Response<List<Event>> response) {
                progressBar.setVisibility(View.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    eventAdapter.updateEvents(response.body());
                }
            }

            @Override
            public void onFailure(Call<List<Event>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Toast.makeText(ProjectDetailActivity.this,
                        "Error loading events", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void updateProjectInfo(Project project) {
        projectNameText.setText(project.getName());
        statusText.setText("Status: " + project.getStatus());
        progressText.setText(String.format("Progress: %d / %d tasks (%d%%)",
                project.getCompletedTasks(),
                project.getTotalTasks(),
                project.getProgressPercentage()));
    }

    private void startAutoRefresh() {
        refreshHandler = new Handler();
        refreshRunnable = new Runnable() {
            @Override
            public void run() {
                loadProjectData();
                refreshHandler.postDelayed(this, 5000); // Refresh every 5 seconds
            }
        };
        refreshHandler.postDelayed(refreshRunnable, 5000);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (refreshHandler != null && refreshRunnable != null) {
            refreshHandler.removeCallbacks(refreshRunnable);
        }
    }
}
