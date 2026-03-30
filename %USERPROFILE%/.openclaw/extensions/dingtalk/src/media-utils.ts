// src/media-utils.ts

/**
 * Media handling utilities for OpenClaw.
 * This module provides functions to process media files in compliance with OpenClaw best practices.
 */

type MediaType = 'image' | 'video' | 'audio';

interface MediaFile {
    type: MediaType;
    url: string;
    size: number;
}

/**
 * Validates the size of a media file.
 * @param file The media file to validate.
 * @param maxSize The maximum allowed size in bytes.
 * @returns true if valid, false otherwise.
 */
function validateMediaSize(file: MediaFile, maxSize: number): boolean {
    return file.size <= maxSize;
}

/**
 * Prepares a media file for upload.
 * @param file The media file to prepare.
 * @returns The prepared media file object.
 */
function prepareMediaFile(file: MediaFile): MediaFile {
    // Add any preparation logic here
    return file;
}

/**
 * Logs media file upload information.
 * @param file The media file being uploaded.
 */
function logMediaUpload(file: MediaFile): void {
    console.log(`Uploading ${file.type} file: ${file.url}, size: ${file.size} bytes.`);
}

export { MediaFile, validateMediaSize, prepareMediaFile, logMediaUpload };