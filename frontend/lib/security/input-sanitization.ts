const CONTROL_CHAR_REGEX = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;
const FILE_PATH_SEPARATORS_REGEX = /[\\/]/g;

export interface SanitizeTextOptions {
  trim?: boolean;
  maxLength?: number;
}

export interface UploadValidationOptions {
  maxSizeBytes?: number;
  allowedMimeTypes?: string[];
  allowedMimePrefixes?: string[];
}

interface UploadValidationResult {
  valid: boolean;
  reason?: string;
}

const DEFAULT_ALLOWED_MIME_TYPES = [
  'application/json',
  'application/msword',
  'application/pdf',
  'application/rtf',
  'application/vnd.ms-excel',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const DEFAULT_ALLOWED_MIME_PREFIXES = ['text/', 'video/'];

const DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
}

export function sanitizeTextInput(rawValue: string, options: SanitizeTextOptions = {}): string {
  const { trim = true, maxLength } = options;

  let nextValue = rawValue.replace(CONTROL_CHAR_REGEX, '');
  nextValue = nextValue.normalize('NFKC');

  if (trim) {
    nextValue = nextValue.trim();
  }

  if (typeof maxLength === 'number' && maxLength > 0) {
    nextValue = nextValue.slice(0, maxLength);
  }

  return nextValue;
}

export function sanitizeFileName(fileName: string): string {
  const cleaned = sanitizeTextInput(fileName, { trim: true, maxLength: 180 });
  return cleaned.replace(FILE_PATH_SEPARATORS_REGEX, '_');
}

export function sanitizeJsonPayload<T>(payload: T): T {
  if (typeof payload === 'string') {
    return sanitizeTextInput(payload, { trim: false }) as T;
  }

  if (Array.isArray(payload)) {
    return payload.map((item) => sanitizeJsonPayload(item)) as T;
  }

  if (isRecord(payload)) {
    const nextPayload: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(payload)) {
      nextPayload[key] = sanitizeJsonPayload(value);
    }
    return nextPayload as T;
  }

  return payload;
}

export function validateUploadFile(
  file: Pick<File, 'name' | 'size' | 'type'>,
  options: UploadValidationOptions = {},
): UploadValidationResult {
  const {
    maxSizeBytes = DEFAULT_MAX_UPLOAD_BYTES,
    allowedMimeTypes = DEFAULT_ALLOWED_MIME_TYPES,
    allowedMimePrefixes = DEFAULT_ALLOWED_MIME_PREFIXES,
  } = options;

  if (file.size <= 0) {
    return { valid: false, reason: 'Empty files are not supported.' };
  }

  if (file.size > maxSizeBytes) {
    return { valid: false, reason: `File exceeds ${Math.floor(maxSizeBytes / (1024 * 1024))}MB limit.` };
  }

  const normalizedType = file.type.toLowerCase();
  const allowedByType = allowedMimeTypes.includes(normalizedType);
  const allowedByPrefix = allowedMimePrefixes.some((prefix) => normalizedType.startsWith(prefix));

  if (!allowedByType && !allowedByPrefix) {
    return {
      valid: false,
      reason: 'Unsupported file type. Use document, text, or video files.',
    };
  }

  return { valid: true };
}
