_tipica() {
    local cur prev1 prev2 prev3cmds
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev1="${COMP_WORDS[COMP_CWORD-1]}"
    prev2="${COMP_WORDS[COMP_CWORD-2]}"
    prev3="${COMP_WORDS[COMP_CWORD-3]}"
    COMPREPLY=()

    if [ "x${USER}" == "xroot" ]; then
        if [ "x${prev1}" == "xtipica" ]; then
            local cmds="status db-init set-user set-image \
                        node-list node-add node-update node-delete \
                        user-list user-add user-update user-delete \
                        image-list image-add image-update image-delete \
                        image-build"
            COMPREPLY=($(compgen -W "${cmds}" -- ${cur}))
        elif [ "x${prev2}" == "xtipica" ]; then
            case "${prev1}" in
            "node-update"|"node-delete"|"set-user"|"set-image")
                COMPREPLY=($(compgen -W "$(tipica node-names)" -- ${cur}))
            ;;
            "user-update"|"user-delete")
                COMPREPLY=($(compgen -W "$(tipica user-names)" -- ${cur}))
            ;;
            "image-update"|"image-delete")
                COMPREPLY=($(compgen -W "$(tipica image-names)" -- ${cur}))
            ;;
            "image-build")
                local available_images="cent7 xenial"
                COMPREPLY=($(compgen -W "${available_images}" -- ${cur}))
            ;;
            esac
        fi
        return
    fi

    if [ "x${prev1}" == "xtipica" ]; then
        local cmds="status acquire switch release pxeboot start shutdown \
                    destroy images login console note version usage"
        COMPREPLY=($(compgen -W "${cmds}" -- ${cur}))
    elif [ "x${prev2}" == "xtipica" ]; then
        case "${prev1}" in
        "acquire")
            COMPREPLY=($(compgen -W "$(tipica node-names-free)" -- ${cur}))
        ;;
        "status"|"switch"|"release"|"pxeboot"|"start"|"shutdown"|\
        "destroy"|"login"|"console"|"note")
            COMPREPLY=($(compgen -W "$(tipica node-names-owned)" -- ${cur}))
        ;;
        esac
    elif [ "x${prev3}" == "xtipica" ]; then
        if [ "x${prev2}" == "xpxeboot" ]; then
            COMPREPLY=($(compgen -W "$(tipica image-names)" -- ${cur}))
        elif [ "x${COMP_WORDS[COMP_CWORD-2]}" == "xswitch" ]; then
            COMPREPLY=($(compgen -W "$(tipica user-names)" -- ${cur}))
        fi
    fi
}
complete -F _tipica tipica
