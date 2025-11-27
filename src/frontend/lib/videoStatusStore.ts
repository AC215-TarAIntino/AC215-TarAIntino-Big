/**
 * In-memory store for tracking video generation status across sessions
 *
 * This store maintains the state of video generation requests so that
 * the status endpoint can check if a video has been completed.
 */

export interface VideoStatus {
  status: "processing" | "complete" | "error";
  gcsUrl?: string;
  publicUrl?: string;
  movieTitle?: string;
  progress: number;
  error?: string;
  timestamp?: number;
}

class VideoStatusStore {
  private store: Map<string, VideoStatus>;

  constructor() {
    this.store = new Map();
  }

  /**
   * Store or update video status for a session
   */
  set(sessionId: string, status: VideoStatus): void {
    this.store.set(sessionId, {
      ...status,
      timestamp: Date.now(),
    });
  }

  /**
   * Retrieve video status for a session
   */
  get(sessionId: string): VideoStatus | undefined {
    return this.store.get(sessionId);
  }

  /**
   * Remove video status for a session
   */
  delete(sessionId: string): boolean {
    return this.store.delete(sessionId);
  }

  /**
   * Clear all stored statuses
   */
  clear(): void {
    this.store.clear();
  }

  /**
   * Get all session IDs
   */
  keys(): string[] {
    return Array.from(this.store.keys());
  }

  /**
   * Clean up old entries (older than 24 hours)
   */
  cleanup(maxAgeMs: number = 24 * 60 * 60 * 1000): void {
    const now = Date.now();
    for (const [sessionId, status] of this.store.entries()) {
      if (status.timestamp && now - status.timestamp > maxAgeMs) {
        this.store.delete(sessionId);
      }
    }
  }
}

// Export a singleton instance
export const videoStatusStore = new VideoStatusStore();
