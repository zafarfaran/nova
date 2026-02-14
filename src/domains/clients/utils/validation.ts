/**
 * Validation utilities for client forms
 */

import type { EntityType } from "../types";

export interface ValidationError {
    field: string;
    message: string;
}

/**
 * Validates email format
 */
export function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim());
}

/**
 * Validates client creation form data
 */
export function validateClientForm(data: {
    name: string;
    email: string;
    entityType: EntityType | string;
}): ValidationError[] {
    const errors: ValidationError[] = [];

    if (!data.name.trim()) {
        errors.push({ field: "name", message: "Client name is required" });
    }

    if (!data.email.trim()) {
        errors.push({ field: "email", message: "Email is required" });
    } else if (!validateEmail(data.email)) {
        errors.push({ field: "email", message: "Please enter a valid email address" });
    }

    if (!data.entityType) {
        errors.push({ field: "entityType", message: "Entity type is required" });
    }

    return errors;
}

/**
 * Gets the first validation error message
 */
export function getFirstValidationError(errors: ValidationError[]): string | null {
    return errors.length > 0 ? errors[0].message : null;
}
