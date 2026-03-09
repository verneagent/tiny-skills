-- open_tab.applescript
-- Opens a new tab in iTerm2 (preferred) or Terminal.app (fallback)
-- and runs the given command.
--
-- Usage: osascript open_tab.applescript "<command>"
-- Example: osascript open_tab.applescript "cd /path && claude"

on run argv
    set cmd to item 1 of argv

    if application "iTerm" is running or (do shell script "ls /Applications/iTerm.app > /dev/null 2>&1 && echo yes || echo no") is "yes" then
        tell application "iTerm"
            activate
            tell current window
                set newTab to (create tab with default profile)
                tell current session of newTab
                    write text cmd
                end tell
            end tell
        end tell
    else
        tell application "Terminal"
            activate
            do script cmd
        end tell
    end if
end run
