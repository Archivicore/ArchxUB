#!/bin/bash

. init/logbot/logbot.sh
. init/proc.sh
. init/utils.sh
. init/checks.sh

trap 'handleSig SIGHUP' HUP
trap 'handleSig SIGTERM' TERM
trap 'handleSig SIGINT' INT
trap '' USR1

handleSig() {
    log "Exiting With $1 ..."
    killProc
}

initArchx() {
    printLogo
    assertPrerequisites
    sendMessage "Initializing Archx ..."
    assertEnvironment
    editLastMessage "Starting Archx ..."
    printLine
}

startArchx() {
    startLogBotPolling
    runPythonModule Archx "$@"
}

stopArchx() {
    sendMessage "Exiting Archx ..."
    endLogBotPolling
}

runArchx() {
    initArchx
    startArchx "$@"
    local code=$?
    stopArchx
    return $code
}
