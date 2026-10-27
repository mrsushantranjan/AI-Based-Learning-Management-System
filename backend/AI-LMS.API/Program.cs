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
var jwtKey = builder.Configuration["Jwt:Key"]
    ?? Environment.GetEnvironmentVariable("JWT_SECRET")
    ?? "Learnova_AI_LMS_Secure_JWT_Key_2026_Enterprise_Edition_256Bits!";

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

// Forwarded headers for reverse proxies (Render, Railway, Docker, Cloudflare)
app.UseForwardedHeaders(new ForwardedHeadersOptions
{
    ForwardedHeaders = Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedFor |
                       Microsoft.AspNetCore.HttpOverrides.ForwardedHeaders.XForwardedProto
});

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

// Production Health Check Endpoints
app.MapGet("/health", () => Results.Ok(new
{
    status = "healthy",
    service = "AI-LMS.API",
    runtime = ".NET 10.0",
    timestamp = DateTime.UtcNow
}));

app.MapGet("/api/health", (MongoDbContext db) => Results.Ok(new
{
    status = "healthy",
    database = db.DatabaseName,
    connection = db.MaskedConnectionString,
    timestamp = DateTime.UtcNow
}));

app.MapControllers();

// Database Seeding (Guarded to prevent data overwrites)
var enableSeeding = builder.Configuration.GetValue<bool>("SeedDatabase", true);
if (enableSeeding)
{
    await DbSeeder.SeedDatabaseAsync(app);
}

app.Run();
