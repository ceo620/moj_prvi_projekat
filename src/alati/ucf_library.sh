# Shared functions for ucf and ucfr

vset() {
    # Value Doc_string
    if [ -z "$1" ]; then
	echo >&2 "$progname: Unable to determine $2"
	exit 1
    else
	if [ -n "$VERBOSE" ]; then
	    echo >&2 "$progname: $2 is $1"
	fi
	printf '%s' "$1"
    fi
}

withecho () {
        echo "$@" >&2
        "$@"
}

escape_bre () {
    printf '%s' "$1" | sed -e 's#[.[\*^$]#\\&#g'
}
