# How to set up a script to execute on boot!

### First we need to tell the Pi that it's okay to execute the script automatically.

Change directory to SDC-UR-DC/code/main
```Bash
cd /home/trash/SDC-UR-DC/code/main
```

Now we need to set executable privileges to all users:

```Bash
chmod a+x start.sh
```

### Next we need to create a Cron job to execute the script on reboot

Open crontab
```Bash
crontab -e
```

It will then ask you what editor you want to use:

```
Select an editor.  To change later, run select-editor again.
* 1. /bin/nano        <---- easiest
  2. /usr/bin/vim.basic
  3. /usr/bin/vim.tiny
  4. /usr/bin/code
  5. /bin/ed

Choose 1-5 [1]: 
```
Select nano, which should be the first option. So type in `1`, then hit Enter.

Now you should see a bunch of text explaining how to use cron.
```bash
    GNU nano 8.4                                                                            
# Edit this file to introduce tasks to be run by cron.
# 
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
# 
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').
# 
# Notice that tasks will be started based on the cron's system
.
.
.
```

We are going to scroll to the very bottom using the arrow keys or mousewheel, and copy & paste or type this:

```Bash
@reboot sleep 5 && /home/trash/SDC-UR-DC/code/main/start.sh > /home/trash/SDC-UR-DC/code/main/start.log 2>&1
```

This is a cronjob that will only start on reboot, wait 5 seconds (to let all system services to start), and then execute start.sh, while outputting any print or error statements to `start.log`.

Now save with `Ctrl + O` and exit with `Ctrl + X`.

## Voila! You're done and the Pi should execute start.sh on reboot now!!