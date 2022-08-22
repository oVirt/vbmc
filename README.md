# gerrit-to-gh
This is a skeleton repository for moving from Gerrit to GitHub. Example README content below. Replace `PROJECTNAME` with your project repository and make sure the Bugzilla link exists if you choose to keep this piece in your README.

---

## Using Actions

You can find details around the syntax in the [official Actions documentation](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions).

There is an example `check-patch.yml` GitHub Action in the `.github/workflows` directory. It uses the `main` branch to execute Actions on pushes and pull requests. The relevant lines are commented out as this Action would fail on this repository. If you choose to let the Action run by commenting the commands back in, you can check the error logs in the `Actions` tab on GitHub and use it in your own repository.

*Note:* This example used with the [right repository](https://github.com/oVirt/ovirt-release/actions) builds rpms on both CentOS Stream 8 and CentOS Stream 9 as explained in the [oVirt Developer Documentation](https://ovirt.org/develop/developer-guide/migrating_to_github.html). If you do not need this example file as a guide, delete it and create your own Actions file.

---

# oVirt PROJECTNAME

Welcome to the oVirt PROJECTNAME source repository. This repository is hosted on [GitHub:PROJECTNAME](https://github.com/oVirt/PROJECTNAME).

## How to contribute

All contributions are welcome - patches, bug reports, and documentation issues.

### Submitting patches

Please submit patches to [GitHub:PROJECTNAME](https://github.com/oVirt/PROJECTNAME). If you are not familiar with the process, you can read about [collaborating with pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests) on the GitHub website.

### Found a bug or documentation issue?

To submit a bug or suggest an enhancement for oVirt PROJECTNAME please use [oVirt Bugzilla](https://bugzilla.redhat.com/enter_bug.cgi?product=PROJECTNAME).

If you don't have a Bugzilla account, you can still report [issues](https://github.com/oVirt/PROJECTNAME/issues). If you find a documentation issue on the oVirt website, please navigate to the page footer and click "Report an issue on GitHub".

## Still need help?

If you have any other questions or suggestions, you can join and contact us on the [oVirt Users forum / mailing list](https://lists.ovirt.org/admin/lists/users.ovirt.org/).