#!/usr/bin/python3
"""
S390xGeneration

This module provides functionality to determine the generation of the
s390x architecture based on the machine type.

Author: Simon Johnsson
Version: 0.0.1
"""

import logging

from enum import Enum, auto


class S390xGeneration(Enum):
    """
    S390xGeneration

    This Enum class provides constants representing different generations
    of the S390x architecture.
    """

    # IMPORTANT: Keep the order of the generations as it is, as the
    # comparison operators depend on it.
    ZEC12 = auto()
    Z13 = auto()
    Z14 = auto()
    Z15 = auto()
    Z16 = auto()
    Z17 = auto()

    def __lt__(self, other: "S390xGeneration") -> bool:
        return self.value < other.value

    def __gt__(self, other: "S390xGeneration") -> bool:
        return self.value > other.value

    def __le__(self, other: "S390xGeneration") -> bool:
        return self.value <= other.value

    def __ge__(self, other: "S390xGeneration") -> bool:
        return self.value >= other.value


def _machine_type_to_generation(machine_type: int) -> S390xGeneration | None:
    """
    Get the S390x generation corresponding to the given machine type.

    Returns:
        S390xGeneration | None: The corresponding S390x generation, or None if
        the machine code is unrecognized.
    """
    mapping: dict[int, S390xGeneration] = {
        # zEC12 machine types
        2827: S390xGeneration.ZEC12,
        2828: S390xGeneration.ZEC12,
        # z13 machine types
        2964: S390xGeneration.Z13,
        2965: S390xGeneration.Z13,
        # z14 machine types
        3906: S390xGeneration.Z14,
        3907: S390xGeneration.Z14,
        # z15 machine types
        8561: S390xGeneration.Z15,
        8562: S390xGeneration.Z15,
        # z16 machine types
        3931: S390xGeneration.Z16,
        3932: S390xGeneration.Z16,
        # z17 machine types
        9175: S390xGeneration.Z17,
        9176: S390xGeneration.Z17,
    }
    return mapping.get(machine_type)


def _read_machine_type() -> int | None:
    """
    Read the machine type from /proc/sysinfo.

    Returns:
        int | None: The machine type as an integer, or None if it cannot be
        determined.
    """
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                key, _, value = line.partition(":")
                if key.strip() == "machine" and value.strip().isdigit():
                    return int(value.strip())
    except (FileNotFoundError, ValueError):
        return None
    return None


def get_system_s390x_generation() -> S390xGeneration | None:
    """
    Return the current running s390x generation, otherwise None if not running
    on s390x architecture or if the generation cannot be determined.
    """
    machine_type = _read_machine_type()
    if machine_type is None:
        logging.warning("Failed to read machine type from /proc/cpuinfo!")
        return None

    return _machine_type_to_generation(machine_type)
