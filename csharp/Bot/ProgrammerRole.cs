﻿using Interfaces;
using Octokit;
using Storage.Remote.GitHub;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace Bot
{
    internal class ProgrammerRole
    {
        private readonly GitHubStorage gitHubAPI;

        private static readonly TimeSpan MinimumInteractionInterval = new(0, 0, 0, 0, 1200);

        private readonly List<ITrigger<Issue>> triggers;

        public ProgrammerRole(List<ITrigger<Issue>> triggers,IRemoteCodeStorage<Issue> gitHubAPI)
        {
            this.gitHubAPI = (GitHubStorage)gitHubAPI;
            this.triggers = triggers;
        }

        private void ProcessIssues(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                var issues = gitHubAPI.GetIssues();
                foreach (var trigger in triggers)
                {
                    foreach (var issue in issues)
                    {
                        if (trigger.Condition(issue))
                        {
                            trigger.Action(issue);
                        }
                    }
                }
                Thread.Sleep(MinimumInteractionInterval);
            }
        }

        public void Start(CancellationToken cancellationToken)
        {
            ProcessIssues(cancellationToken);
        }
    }
}