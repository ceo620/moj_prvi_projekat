#!/data/data/com.termux/files/usr/bin/bash

export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH="$PREFIX/bin:$PREFIX/bin/applets"
export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"

LOG="$HOME/HUMAN_GATE_COMMAND_CENTER/08_CRON_REPAIR/CMU_BOOT_RUNTIME.log"

{
  echo "============================================================"
  echo "BOOT_TIME=$(date)"
  echo "HUMAN_GATE=Danijela_Djurovic_Keskin"
  echo "PROTOKOL=888"
  echo "AUTOMATIC_DELETE=NO"

  sleep 20

  if ! pgrep -x runsvdir >/dev/null 2>&1; then
    nohup runsvdir "$SVDIR" >> "$LOG" 2>&1 &
    sleep 3
  fi

  sv up crond
  sleep 2
  sv status crond

  echo "SSHD_RUNNING_COUNT=$(pgrep -x sshd 2>/dev/null | wc -l)"
  echo "SSH_AGENT_RUNNING_COUNT=$(pgrep -x ssh-agent 2>/dev/null | wc -l)"
  echo "FINAL_STATUS=CMU_CRON_BOOT_ATTEMPT_COMPLETED"
} >> "$LOG" 2>&1
