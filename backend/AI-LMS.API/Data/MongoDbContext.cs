using MongoDB.Driver;
using AI_LMS.API.Models;

namespace AI_LMS.API.Data;

public class MongoDbContext
{
    private readonly IMongoDatabase _database;

    public MongoDbContext(IConfiguration configuration)
    {
        var connectionString =
            configuration["MongoDB:ConnectionString"];

        var databaseName =
            configuration["MongoDB:DatabaseName"];

        var client = new MongoClient(connectionString);

        _database = client.GetDatabase(databaseName);
    }

    public IMongoDatabase Database => _database;

    public string DatabaseName => _database.DatabaseNamespace.DatabaseName;

    public IMongoCollection<User> Users =>
        _database.GetCollection<User>("users");

    public IMongoCollection<Course> Courses =>
        _database.GetCollection<Course>("courses");

    public IMongoCollection<Faculty> Faculty =>
        _database.GetCollection<Faculty>("faculty");

    public IMongoCollection<Enrollment> Enrollments =>
        _database.GetCollection<Enrollment>("enrollments");

    public IMongoCollection<StudentProgress> StudentProgress =>
        _database.GetCollection<StudentProgress>("studentProgress");

    public IMongoCollection<Certificate> Certificates =>
        _database.GetCollection<Certificate>("certificates");
}