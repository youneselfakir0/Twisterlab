import { useTelemetry as useTelemetryFromContext } from '../context/TelemetryContext';

/**
 * Senior Staff Hook Redirect
 * Centralizes the telemetry stream to a single WebSocket instance via Context API.
 * This prevents the "multiple connections" bug while maintaining compatibility.
 */
export const useTelemetry = () => {
  return useTelemetryFromContext();
};
