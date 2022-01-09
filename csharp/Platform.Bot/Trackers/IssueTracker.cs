using Interfaces;
using Octokit;
using Storage.Remote.GitHub;
using System;
using System.Collections.Generic;
using System.Threading;

namespace Platform.Bot.Trackers
{
    /// <summary>
    /// <para>
    /// Represents the programmer role.
    /// </para>
    /// <para></para>
    /// </summary>
    public class IssueTracker : ITracker<Issue>
    {
        /// <summary>
        /// <para>
        /// The git hub api.
        /// </para>
        /// <para></para>
        /// </summary>
        public GitHubStorage GitHubApi { get; }

        /// <summary>
        /// <para>
        /// The minimum interaction interval.
        /// </para>
        /// <para></para>
        /// </summary>
        public TimeSpan MinimumInteractionInterval { get; }

        /// <summary>
        /// <para>
        /// The triggers.
        /// </para>
        /// <para></para>
        /// </summary>
        public List<ITrigger<Issue>> Triggers { get; }

        /// <summary>
        /// <para>
        /// Initializes a new <see cref="IssueTracker"/> instance.
        /// </para>
        /// <para></para>
        /// </summary>
        /// <param name="triggers">
        /// <para>A triggers.</para>
        /// <para></para>
        /// </param>
        /// <param name="gitHubAPI">
        /// <para>A git hub api.</para>
        /// <para></para>
        /// </param>
        public IssueTracker(List<ITrigger<Issue>> triggers, GitHubStorage gitHubApi)
        {
            GitHubApi = gitHubApi;
            Triggers = triggers;
            MinimumInteractionInterval = gitHubApi.MinimumInteractionInterval;
        }


        /// <summary>
        /// <para>
        /// Starts the cancellation token.
        /// </para>
        /// <para></para>
        /// </summary>
        /// <param name="cancellationToken">
        /// <para>The cancellation token.</para>
        /// <para></para>
        /// </param>
        public void Start(CancellationToken cancellationToken)
        {
            Console.WriteLine("issue Trecker has been started");
            while (!cancellationToken.IsCancellationRequested)
            {
                foreach (var trigger in Triggers)
                {
                    try
                    {
                        foreach (var issue in GitHubApi.GetIssues())
                        {
                            if (trigger.Condition(issue))
                            {
                                trigger.Action(issue);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine(ex);
                    }
                }
                Thread.Sleep(MinimumInteractionInterval);
            }
        }
    }
}
