package com.softsmith.maker;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
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
 * Main activity showing list of projects
 */
public class MainActivity extends AppCompatActivity {

    private RecyclerView recyclerView;
    private ProjectAdapter adapter;
    private ProgressBar progressBar;
    private EditText promptInput;
    private Button createButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupRecyclerView();
        loadProjects();
    }

    private void initViews() {
        recyclerView = findViewById(R.id.recyclerView);
        progressBar = findViewById(R.id.progressBar);
        promptInput = findViewById(R.id.promptInput);
        createButton = findViewById(R.id.createButton);

        createButton.setOnClickListener(v -> createProject());
    }

    private void setupRecyclerView() {
        adapter = new ProjectAdapter(new ArrayList<>(), project -> {
            Intent intent = new Intent(MainActivity.this, ProjectDetailActivity.class);
            intent.putExtra("project_id", project.getId());
            intent.putExtra("project_name", project.getName());
            startActivity(intent);
        });

        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        recyclerView.setAdapter(adapter);
    }

    private void loadProjects() {
        progressBar.setVisibility(View.VISIBLE);

        ApiClient.getApiService().getProjects(50, 0).enqueue(new Callback<List<Project>>() {
            @Override
            public void onResponse(Call<List<Project>> call, Response<List<Project>> response) {
                progressBar.setVisibility(View.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    adapter.updateProjects(response.body());
                } else {
                    Toast.makeText(MainActivity.this,
                        "Failed to load projects", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<Project>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Toast.makeText(MainActivity.this,
                    "Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void createProject() {
        String prompt = promptInput.getText().toString().trim();

        if (prompt.isEmpty()) {
            Toast.makeText(this, "Please enter a project description",
                Toast.LENGTH_SHORT).show();
            return;
        }

        progressBar.setVisibility(View.VISIBLE);
        createButton.setEnabled(false);

        CreateProjectRequest request = new CreateProjectRequest(prompt, null, "android-user");

        ApiClient.getApiService().createProject(request).enqueue(new Callback<Project>() {
            @Override
            public void onResponse(Call<Project> call, Response<Project> response) {
                progressBar.setVisibility(View.GONE);
                createButton.setEnabled(true);

                if (response.isSuccessful()) {
                    promptInput.setText("");
                    Toast.makeText(MainActivity.this,
                        "Project created!", Toast.LENGTH_SHORT).show();
                    loadProjects();  // Refresh list
                } else {
                    Toast.makeText(MainActivity.this,
                        "Failed to create project", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<Project> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                createButton.setEnabled(true);
                Toast.makeText(MainActivity.this,
                    "Error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadProjects();  // Refresh when returning to activity
    }
}
