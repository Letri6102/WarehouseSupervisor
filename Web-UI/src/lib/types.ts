export type LogLevel = "INFO" | "WARN" | "ERROR";

export type LogEntry = {
  id: string;
  ts: number; // epoch ms
  level: LogLevel;
  source: "webcam" | "upload" | "system";
  message: string;
  data?: Record<string, any>;
};
