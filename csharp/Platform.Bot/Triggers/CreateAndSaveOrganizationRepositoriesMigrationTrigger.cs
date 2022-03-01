using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Interfaces;
using Octokit;
using Platform.Data;
using Platform.Data.Doublets;
using Platform.Timestamps;
using Storage.Local;
using Storage.Remote.GitHub;

namespace Platform.Bot.Triggers;

public class CreateAndSaveOrganizationRepositoriesMigrationTrigger : ITrigger<DateTime?>
{
    private readonly GitHubStorage _githubStorage;

    private readonly FileStorage _linksStorage;

    private string _filePath;

    public CreateAndSaveOrganizationRepositoriesMigrationTrigger(GitHubStorage githubStorage, FileStorage linksStorage, string filePath)
    {
        _githubStorage = githubStorage;
        _linksStorage = linksStorage;
        _filePath = filePath;

    }
    public bool Condition(DateTime? dateTime)
    {
        var allMigrations = _githubStorage.GetAllMigrations("linksplatform");
        if (allMigrations.Count == 0)
        {
            return true;
        }
        var lastMigrationTimestamp = Convert.ToDateTime(allMigrations.Last().CreatedAt);
        var timeAfterLastMigration = DateTime.Now - lastMigrationTimestamp;
        return timeAfterLastMigration.Days > 1;
    }

    public async void Action(DateTime? dateTime)
    {
        var repositoryNames = _githubStorage.GetAllRepositoryNames("linksplatform");
        var createMigrationResult = await _githubStorage.CreateMigration("linksplatform", repositoryNames);
        if (null == createMigrationResult || createMigrationResult.State.Value == Migration.MigrationState.Failed)
        {
            Console.WriteLine("Migration is failed.");
            return;
        }
        Console.WriteLine($"Saving migration {createMigrationResult.Id}.");
        await _githubStorage.SaveMigrationArchive("linksplatform", createMigrationResult.Id, _filePath);
        Console.WriteLine($"Migration {createMigrationResult.Id} is saved.");
    }
}