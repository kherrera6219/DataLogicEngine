/**
 * Zod validation schemas for UKG System
 */

import { z } from 'zod'

// User registration schema
export const registerSchema = z.object({
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and hyphens'),
  email: z.string()
    .email('Invalid email address')
    .max(255, 'Email must be less than 255 characters'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[!@#$%^&*]/, 'Password must contain at least one special character (!@#$%^&*)'),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
})

// Login schema
export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  role: z.enum(['acquisition', 'industry', 'regulatory', 'compliance']).optional(),
  simulationMode: z.boolean().optional(),
})

// Chat query schema
export const chatQuerySchema = z.object({
  query: z.string()
    .min(1, 'Query cannot be empty')
    .max(5000, 'Query must be less than 5000 characters'),
  target_confidence: z.number()
    .min(0.6, 'Confidence threshold must be at least 0.6')
    .max(0.95, 'Confidence threshold cannot exceed 0.95')
    .optional(),
  chat_id: z.string().uuid().optional().nullable(),
  use_location_context: z.boolean().optional(),
  use_research_agents: z.boolean().optional(),
  active_personas: z.array(z.enum(['KE', 'SE', 'RE', 'CE'])).optional(),
})

// Simulation parameters schema
export const simulationParamsSchema = z.object({
  name: z.string()
    .min(1, 'Simulation name is required')
    .max(100, 'Simulation name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  sim_type: z.enum(['knowledge_graph', 'persona_analysis', 'location_context', 'time_analysis']),
  refinement_steps: z.number()
    .int('Refinement steps must be an integer')
    .min(1, 'At least 1 refinement step required')
    .max(20, 'Maximum 20 refinement steps allowed')
    .default(12),
  confidence_threshold: z.number()
    .min(0.6)
    .max(0.95)
    .default(0.85),
  entropy_sampling: z.boolean().default(false),
  auto_start: z.boolean().default(false),
})

// API key schema
export const apiKeySchema = z.object({
  name: z.string()
    .min(1, 'API key name is required')
    .max(100, 'API key name must be less than 100 characters'),
  permissions: z.array(z.enum(['read', 'write', 'admin'])),
  expires_at: z.string().datetime().optional(),
})

// File upload schema
export const fileUploadSchema = z.object({
  file: z.instanceof(File)
    .refine((file) => file.size <= 10 * 1024 * 1024, 'File size must be less than 10MB')
    .refine(
      (file) => ['application/pdf', 'text/plain', 'application/json'].includes(file.type),
      'File must be PDF, TXT, or JSON'
    ),
  description: z.string().max(500).optional(),
})

// Environment variable schema
export const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url().optional(),
  NEXT_PUBLIC_CORE_UKG_URL: z.string().url().optional(),
  SECRET_KEY: z.string().min(32, 'SECRET_KEY must be at least 32 characters'),
  JWT_SECRET_KEY: z.string().min(32, 'JWT_SECRET_KEY must be at least 32 characters'),
  DATABASE_URL: z.string().optional(),
  FLASK_ENV: z.enum(['development', 'testing', 'production']).optional(),
  NODE_ENV: z.enum(['development', 'test', 'production']).optional(),
  CORS_ORIGINS: z.string().optional(),
})

// Export types
export type RegisterInput = z.infer<typeof registerSchema>
export type LoginInput = z.infer<typeof loginSchema>
export type ChatQueryInput = z.infer<typeof chatQuerySchema>
export type SimulationParamsInput = z.infer<typeof simulationParamsSchema>
export type ApiKeyInput = z.infer<typeof apiKeySchema>
export type FileUploadInput = z.infer<typeof fileUploadSchema>
export type EnvVariables = z.infer<typeof envSchema>
