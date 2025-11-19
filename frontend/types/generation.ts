export interface AssetInfo {
  path: string;
  gcs_uri: string;
  public_url: string;
}

export interface TrailerGenerationResponse {
  character_refs: Record<string, AssetInfo>;
  scene_videos: AssetInfo[];
  trailer?: AssetInfo | null;
}
