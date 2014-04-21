#!/bin/bash

# ch build <id>...     build the current package for multiple chroots
# ch clean             remove all working copies
# ch install <id> <package files>...  install the package files in the chroot
# ch kill all          remove all chroots (including master chroot)
# ch update            update all chroots
# ch list              lists all existing master chroots

# IDs work like this:
# 64    = 64bit extra
# 64t   = 64bit testing
# 64ml  = 64bit multilib
# 64mlt = 64bit multilib testing
#
# 64+foo = 64 extra, but different working copy

# functions for building chroots
CHROOTS="/mnt/msata/chroots/arch"

shopt -s nullglob

__genchroot() {
	sudo btrfs subvolume snapshot "$chrootdir/root" "$copydir"
}

__chrootalias() {
	chroot=""
	chroot_arch=""
	arg_arch=${1%%+*}
	arg_copy="$USER+$1"
	arg_copy=${arg_copy//+/-}

	case $arg_arch in
		32*)
			chroot_arch=32
			case $arg_arch in
				32) chroot=extra-i686;;
				32t) chroot=testing-i686;;
				32s) chroot=staging-i686;;
			esac
			;;
		64*)
			chroot_arch=64;
			case $arg_arch in
				64) chroot=extra-x86_64;;
				64t) chroot=testing-x86_64;;
				64s) chroot=staging-x86_64;;
				64ml) chroot=multilib-x86_64;;
				64mlt) chroot=multilib-testing-x86_64;;
				64mls) chroot=multilib-staging-x86_64;;
			esac
			;;
		*)
			chroot=$arg_arch
			case $arg_arch in
				*-i686) chroot_arch=32;;
				*-x86_64|multilib*) chroot_arch=64;;
			esac
	esac

	if [[ -z $chroot || -z $chroot_arch ]]; then
		echo "failed to determine chroot for \"$arg_arch\""
		return 1
	fi

	chrootdir="$CHROOTS/$chroot"
	copydir="$chrootdir/$arg_copy"

	# create chroot if necessary
	if [[ ! -d "$chrootdir/root" ]]; then
		# fix command for multilib
		case $chroot in
			multilib*) chroot_cmd="${chroot%%-x86_64}";;
			*) chroot_cmd="$chroot";;
		esac
		cd /var/empty
		sudo "${chroot_cmd}-build" -c -r "$CHROOTS" || true
		cd -
	fi
}

chkill() {
	if [[ $1 = all ]]; then
		for chrootdir in "$CHROOTS/"*/; do
			chkill "$(basename "$chrootdir")"
		done
		return
	fi

	__chrootalias "$1" || return
	for dir in "$CHROOTS/$chroot/"*/; do
		sudo btrfs subvolume delete "$dir"
	done
	sudo rm -rf "$CHROOTS/$chroot"
}

chshell() {
	__chrootalias "$1" || return
	[ -d "$copydir" ] || __genchroot
	sudo arch-nspawn "$copydir" "${2:-/bin/bash}" "${@:3}"
}

chbuild() {
	__chrootalias "$1" || return
	linux${chroot_arch} sudo makechrootpkg -l "${copydir##*/}" -r "$chrootdir" -n -- -f "${@:2}"
	chshell "$1" pacman --noconfirm -Rcs namcap
}

chinstall() {
	__chrootalias $1 || return; shift
	for file in "$@"; do
		files+=("$(readlink -f "$file")")
	done
	cd /var/empty
	linux${chroot_arch} sudo makechrootpkg -l "${copydir##*/}" -r "$chrootdir" -I "${files[@]}"
}

chclean() {
	__chrootalias $1 || return
	for copy in $chrootdir/*/; do
		if [[ $copy = */root/ ]]; then
			continue
		fi

		sudo btrfs subvolume delete "$copy"
		sudo rm -f "${copy%/}.lock"
	done
}

chrshell() {
	__chrootalias $1 || return
	sudo arch-nspawn "$chrootdir/root" "${2:-/bin/bash}" "${@:3}"
}

chupdate() {
	__chrootalias $1 || return
	echo ":: Updating $chroot"
	sudo arch-nspawn "$chrootdir/root" pacman -Syyu --noconfirm
	echo ":: Cleaning up ..."
	chclean $1
}

command=$1; shift
case $command in
	repack)
		for arg; do
			chbuild "$arg" -R
		done
		;;
	build)
		for arg; do
			chbuild "$arg"
		done
		;;
	build-single)
		chbuild "$@"
		;;
	update)
		if [[ $# = 0 ]]; then
			for chrootdir in "$CHROOTS/"*/; do
				chupdate "$(basename "$chrootdir")"
			done
		else
			for arg; do
				chupdate "$arg"
			done
		fi
		;;
	clean)
		if [[ $# = 0 ]]; then
			for chrootdir in "$CHROOTS/"*/; do
				chclean "$(basename "$chrootdir")"
			done
		else
			for arg; do
				chclean "$arg"
			done
		fi
		;;
	kill)
		for arg; do
			chkill $arg
		done
		;;
	shell) chshell "$@";;
	rshell) chrshell "$@";;
	install) chinstall "$@";;
	list)
		for chrootdir in "$CHROOTS/"*/; do
			echo "$(basename "$chrootdir")"
		done
		;;
	*) printf "Unknown command %s\n" "$command";;
esac
