
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "UKG .NET Core Service", Version = "v1" });
});

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(
        policy =>
        {
            policy.AllowAnyOrigin()
                  .AllowAnyHeader()
                  .AllowAnyMethod();
        });
});

// Configure logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "UKG .NET Core Service v1"));
}

app.UseHttpsRedirection();
app.UseRouting();
app.UseCors();
app.UseAuthorization();

// Define resource model
public class UkgResource
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public Dictionary<string, object> Properties { get; set; } = new();
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

// In-memory data store
var resources = new List<UkgResource>
{
    new UkgResource
    {
        Name = "Sample Resource 1",
        Type = "Entity",
        Properties = new Dictionary<string, object>
        {
            { "description", "Example UKG resource from .NET service" },
            { "priority", 1 },
            { "tags", new[] { "sample", "entity", "dotnet" } }
        }
    },
    new UkgResource
    {
        Name = "Sample Resource 2",
        Type = "Relationship",
        Properties = new Dictionary<string, object>
        {
            { "description", "Example relationship resource" },
            { "source", "Entity1" },
            { "target", "Entity2" },
            { "relationship_type", "CONNECTS_TO" }
        }
    }
};

// Health check endpoint
app.MapGet("/health", () =>
{
    return Results.Ok(new
    {
        Status = "healthy",
        Service = "UKG .NET Core Service",
        Timestamp = DateTime.UtcNow,
        Version = "1.0.0"
    });
});

// API endpoints
app.MapGet("/api/resources", () =>
{
    return Results.Ok(new
    {
        Success = true,
        Count = resources.Count,
        Resources = resources,
        Timestamp = DateTime.UtcNow
    });
});

app.MapGet("/api/resources/{id}", (string id) =>
{
    var resource = resources.FirstOrDefault(r => r.Id == id);
    if (resource == null)
    {
        return Results.NotFound(new
        {
            Success = false,
            Message = $"Resource with id {id} not found",
            Timestamp = DateTime.UtcNow
        });
    }

    return Results.Ok(new
    {
        Success = true,
        Resource = resource,
        Timestamp = DateTime.UtcNow
    });
});

app.MapPost("/api/resources", async (HttpRequest request) =>
{
    try
    {
        var requestBody = await JsonSerializer.DeserializeAsync<UkgResource>(request.Body);
        if (requestBody == null)
        {
            return Results.BadRequest(new
            {
                Success = false,
                Message = "Invalid request body",
                Timestamp = DateTime.UtcNow
            });
        }

        // Set ID and created timestamp
        requestBody.Id = Guid.NewGuid().ToString();
        requestBody.CreatedAt = DateTime.UtcNow;

        // Add to in-memory store
        resources.Add(requestBody);

        return Results.Created($"/api/resources/{requestBody.Id}", new
        {
            Success = true,
            Message = "Resource created successfully",
            Resource = requestBody,
            Timestamp = DateTime.UtcNow
        });
    }
    catch (JsonException ex)
    {
        return Results.BadRequest(new
        {
            Success = false,
            Message = "Invalid JSON in request body",
            Error = ex.Message,
            Timestamp = DateTime.UtcNow
        });
    }
    catch (Exception ex)
    {
        return Results.StatusCode(500, new
        {
            Success = false,
            Message = "Error creating resource",
            Error = ex.Message,
            Timestamp = DateTime.UtcNow
        });
    }
});

// Specialized UKG integration endpoints
app.MapGet("/api/graph/analyze", () =>
{
    // Simulate complex graph analysis
    return Results.Ok(new
    {
        Success = true,
        Analysis = new
        {
            NodeCount = 1243,
            EdgeCount = 5678,
            Density = 0.45,
            CommunityCount = 12,
            TopCommunities = new[]
            {
                new { Name = "Financial", NodeCount = 245 },
                new { Name = "Healthcare", NodeCount = 198 },
                new { Name = "Technology", NodeCount = 156 }
            }
        },
        ProcessingTime = 1.23,
        Timestamp = DateTime.UtcNow
    });
});

// Start the application
var port = Environment.GetEnvironmentVariable("DOTNET_PORT") ?? "5005";
app.Run($"http://0.0.0.0:{port}");
