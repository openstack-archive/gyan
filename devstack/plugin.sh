# gyan - Devstack extras script to install gyan

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

echo_summary "gyan's plugin.sh was called..."
source $DEST/gyan/devstack/lib/gyan
(set -o posix; set)

if is_service_enabled gyan-api gyan-compute; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing gyan"
        install_gyan

        install_gyanclient
        cleanup_gyan

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring gyan"
        configure_gyan

        if is_service_enabled key; then
            create_gyan_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize gyan
        init_gyan

        # Start the gyan API and gyan compute
        echo_summary "Starting gyan"
        start_gyan

    fi

    if [[ "$1" == "unstack" ]]; then
        stop_gyan
    fi

    if [[ "$1" == "clean" ]]; then
        cleanup_gyan
    fi
fi

# Restore xtrace
$XTRACE
