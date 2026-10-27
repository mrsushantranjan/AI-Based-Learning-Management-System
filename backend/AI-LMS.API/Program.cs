using AI_LMS.API.Data;
using AI_LMS.API.Services;
using AI_LMS.API.AI.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;

var builder = WebApplication.CreateBuilder(args);

// Controllers
builder.Services.AddControllers();

// MongoDB & Services
builder.Services.AddSingleton<MongoDbContext>();
builder.Services.AddHttpClient();
builder.Services.AddScoped<AuthService>();
builder.Services.AddScoped<IGeminiService, GeminiService>();
builder.Services.AddScoped<GeminiService>();
builder.Services.AddScoped<ProgressService>();

// JWT Authentication
var configJwtKey = builder.Configuration["Jwt:Key"];
var envJwtKey = Environment.GetEnvironmentVariable("JWT_SECRET") ?? Environment.GetEnvironmentVariable("Jwt__Key");
var jwtKey = !string.IsNullOrWhiteSpace(envJwtKey)
    ? envJwtKey
    : (!string.IsNullOrWhiteSpace(configJwtKey)
        ? configJwtKey
        : "Learnova_AI_LMS_Secure_JWT_Key_2026_Enterprise_Edition_256Bits!");

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme =
        JwtBearerDefaults.AuthenticationScheme;

    options.DefaultChallengeScheme =
        JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,

        ValidIssuer = builder.Configuration["Jwt:Issuer"] ?? "AI-LMS",
        ValidAudience = builder.Configuration["Jwt:Audience"] ?? "AI-LMS-Users",

        IssuerSigningKey =
            new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(jwtKey)
            )
    };
});

// Authorization
builder.Services.AddAuthorization();

// CORS Policy
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        var frontendUrl = Environment.GetEnvironmentVariable("FRONTEND_URL");
        if (!string.IsNullOrWhiteSpace(frontendUrl))
        {
            policy.WithOrigins(
                    frontendUrl.TrimEnd('/'),
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "https://localhost:5173"
                  )
                  .AllowAnyHeader()
                  .AllowAnyMethod()
                  .AllowCredentials();
        }
        else
        {
            policy.SetIsOriginAllowed(_ => true)
                  .AllowAnyHeader()
                  .AllowAnyMethod()
                  .AllowCredentials();
        }
    });
});

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Global Exception Diagnostics Handler (Never silent 500)
app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        context.Response.StatusCode = 500;
        context.Response.ContentType = "application/json";
        var feature = context.Features.Get<Microsoft.AspNetCore.Diagnostics.IExceptionHandlerPathFeature>();
        var ex = feature?.Error;
        await context.Response.WriteAsJsonAsync(new
        {
            error = "Server Exception",
            message = ex?.Message,
            type = ex?.GetType().Name
        });
    });
});

// Forwarded headers for reverse proxies (Render, Railway, Docker, Cloudflare)
app.UseForwardedHeaders(new ForwardedHeadersOptions
{
    ForwardedHeaders = Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedFor |
                       Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedProto
});

// Production Health Check Endpoint (Early in pipeline to always succeed independently)
app.MapGet("/health", () => Results.Ok(new
{
    status = "healthy",
    service = "AI-LMS.API",
    runtime = ".NET 10.0",
    timestamp = DateTime.UtcNow
}));

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/api/health", (MongoDbContext db) => Results.Ok(new
{
    status = "healthy",
    database = db.DatabaseName,
    connection = db.MaskedConnectionString,
    timestamp = DateTime.UtcNow
}));

app.MapControllers();

// Database Seeding (Guarded to avoid killing the container if Atlas is still connecting)
var enableSeeding = builder.Configuration.GetValue<bool>("SeedDatabase", true);
if (enableSeeding)
{
    try
    {
        await DbSeeder.SeedDatabaseAsync(app);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Startup Warning] Database seeding skipped or encountered error: {ex.Message}");
    }
}

app.Run();
