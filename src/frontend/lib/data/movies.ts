export interface Movie {
  id: number;
  title: string;
  year: number;
  director: string;
  poster: string;
  tags: string[];
  tagScores: { [key: string]: number };
  description: string;
  color: string; // Dominant color for effects
}

export const TAG_DEFINITIONS = {
  // Visual Style
  noir: "Film noir aesthetic with dark shadows",
  vibrant: "Colorful and visually striking",
  gritty: "Raw and realistic visual style",
  whimsical: "Playful and imaginative visuals",
  minimalist: "Clean, sparse visual approach",

  // Mood
  dark: "Somber or ominous atmosphere",
  uplifting: "Positive and inspirational",
  melancholic: "Sad or wistful tone",
  thrilling: "Exciting and suspenseful",
  contemplative: "Thoughtful and reflective",

  // Themes
  dystopian: "Bleak future society",
  romantic: "Love and relationships focused",
  philosophical: "Deep existential questions",
  violent: "Contains significant violence",
  comedic: "Humorous and funny",
  surreal: "Dream-like or bizarre",
  political: "Commentary on power/society",

  // Genre markers
  scifi: "Science fiction elements",
  horror: "Frightening or disturbing",
  action: "High-energy sequences",
  drama: "Character-driven narrative",
  mystery: "Puzzle or investigation",

  // Pacing/Structure
  slowburn: "Deliberately paced",
  fastpaced: "Quick cutting, energetic",
  nonlinear: "Unconventional timeline",

  // Emotional tone
  heartwarming: "Emotionally touching",
  intense: "Emotionally demanding",
  quirky: "Unusual and eccentric",
};

export const MOVIES: Movie[] = [
  {
    id: 1,
    title: "Blade Runner",
    year: 1982,
    director: "Ridley Scott",
    poster: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&h=600&fit=crop",
    tags: ["noir", "scifi", "dystopian", "philosophical", "dark", "slowburn"],
    tagScores: { noir: 0.95, scifi: 0.98, dystopian: 0.92, philosophical: 0.88, dark: 0.85, slowburn: 0.78 },
    description: "A blade runner must pursue rogue replicants in a dystopian future Los Angeles.",
    color: "#1a1a2e"
  },
  {
    id: 2,
    title: "Inception",
    year: 2010,
    director: "Christopher Nolan",
    poster: "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400&h=600&fit=crop",
    tags: ["scifi", "thriller", "philosophical", "complex", "action", "surreal"],
    tagScores: { scifi: 0.85, thrilling: 0.92, philosophical: 0.80, action: 0.88, surreal: 0.85, fastpaced: 0.75 },
    description: "A thief who steals corporate secrets through dream-sharing technology.",
    color: "#0f4c75"
  },
  {
    id: 3,
    title: "Pulp Fiction",
    year: 1994,
    director: "Quentin Tarantino",
    poster: "https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop",
    tags: ["nonlinear", "violent", "comedic", "stylish", "dialogue-driven", "crime"],
    tagScores: { nonlinear: 0.95, violent: 0.88, comedic: 0.75, quirky: 0.82, fastpaced: 0.70 },
    description: "Various interconnected stories of Los Angeles criminals.",
    color: "#d4a574"
  },
  {
    id: 4,
    title: "Parasite",
    year: 2019,
    director: "Bong Joon-ho",
    poster: "https://images.unsplash.com/photo-1616530940355-351fabd9524b?w=400&h=600&fit=crop",
    tags: ["thriller", "dark", "political", "satire", "class-conscious", "intense"],
    tagScores: { thrilling: 0.90, dark: 0.85, political: 0.92, intense: 0.88, drama: 0.85 },
    description: "A poor family schemes to become employed by a wealthy family.",
    color: "#2d3436"
  },
  {
    id: 5,
    title: "The Grand Budapest Hotel",
    year: 2014,
    director: "Wes Anderson",
    poster: "https://images.unsplash.com/photo-1518929458119-e5bf444c30f4?w=400&h=600&fit=crop",
    tags: ["whimsical", "vibrant", "comedic", "quirky", "stylish", "heartwarming"],
    tagScores: { whimsical: 0.98, vibrant: 0.95, comedic: 0.85, quirky: 0.92, heartwarming: 0.78 },
    description: "The adventures of a legendary concierge at a famous European hotel.",
    color: "#ff6b9d"
  },
  {
    id: 6,
    title: "Mad Max: Fury Road",
    year: 2015,
    director: "George Miller",
    poster: "https://images.unsplash.com/photo-1616530940355-351fabd9524b?w=400&h=600&fit=crop",
    tags: ["action", "dystopian", "intense", "vibrant", "fastpaced", "visceral"],
    tagScores: { action: 0.98, dystopian: 0.95, intense: 0.92, vibrant: 0.88, fastpaced: 0.95 },
    description: "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler.",
    color: "#ff6b35"
  },
  {
    id: 7,
    title: "Amélie",
    year: 2001,
    director: "Jean-Pierre Jeunet",
    poster: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=600&fit=crop",
    tags: ["whimsical", "romantic", "vibrant", "heartwarming", "quirky", "uplifting"],
    tagScores: { whimsical: 0.95, romantic: 0.88, vibrant: 0.92, heartwarming: 0.90, quirky: 0.85, uplifting: 0.88 },
    description: "A shy waitress decides to change the lives of those around her.",
    color: "#e74c3c"
  },
  {
    id: 8,
    title: "Drive",
    year: 2011,
    director: "Nicolas Winding Refn",
    poster: "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=400&h=600&fit=crop",
    tags: ["noir", "stylish", "violent", "minimalist", "slowburn", "atmospheric"],
    tagScores: { noir: 0.88, violent: 0.85, minimalist: 0.90, slowburn: 0.85, dark: 0.80 },
    description: "A mysterious Hollywood stunt driver moonlights as a getaway driver.",
    color: "#ff0066"
  },
  {
    id: 9,
    title: "Her",
    year: 2013,
    director: "Spike Jonze",
    poster: "https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=400&h=600&fit=crop",
    tags: ["scifi", "romantic", "philosophical", "melancholic", "contemplative", "minimalist"],
    tagScores: { scifi: 0.78, romantic: 0.92, philosophical: 0.88, melancholic: 0.85, contemplative: 0.90, minimalist: 0.82 },
    description: "A lonely writer develops an unlikely relationship with an operating system.",
    color: "#ff6b6b"
  },
  {
    id: 10,
    title: "Interstellar",
    year: 2014,
    director: "Christopher Nolan",
    poster: "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=600&fit=crop",
    tags: ["scifi", "philosophical", "emotional", "epic", "contemplative", "visually stunning"],
    tagScores: { scifi: 0.95, philosophical: 0.85, intense: 0.82, contemplative: 0.88, drama: 0.80 },
    description: "A team of explorers travel through a wormhole in space seeking to ensure humanity's survival.",
    color: "#1e3a5f"
  },
  {
    id: 11,
    title: "Moonlight",
    year: 2016,
    director: "Barry Jenkins",
    poster: "https://images.unsplash.com/photo-1492619392994-8a3a63a5ff0f?w=400&h=600&fit=crop",
    tags: ["intimate", "melancholic", "contemplative", "vibrant", "heartfelt", "drama"],
    tagScores: { melancholic: 0.85, contemplative: 0.90, vibrant: 0.78, drama: 0.92, intimate: 0.88 },
    description: "A young black man grapples with his identity and sexuality.",
    color: "#4a00e0"
  },
  {
    id: 12,
    title: "Eternal Sunshine of the Spotless Mind",
    year: 2004,
    director: "Michel Gondry",
    poster: "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=400&h=600&fit=crop",
    tags: ["romantic", "surreal", "philosophical", "melancholic", "quirky", "innovative"],
    tagScores: { romantic: 0.90, surreal: 0.92, philosophical: 0.85, melancholic: 0.88, quirky: 0.80 },
    description: "A couple undergo a procedure to erase each other from their memories.",
    color: "#ffd32a"
  },
  {
    id: 13,
    title: "The Matrix",
    year: 1999,
    director: "Wachowskis",
    poster: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&h=600&fit=crop",
    tags: ["scifi", "action", "philosophical", "dystopian", "groundbreaking", "dark"],
    tagScores: { scifi: 0.95, action: 0.92, philosophical: 0.88, dystopian: 0.85, dark: 0.75 },
    description: "A computer hacker learns the true nature of reality.",
    color: "#00ff41"
  },
  {
    id: 14,
    title: "No Country for Old Men",
    year: 2007,
    director: "Coen Brothers",
    poster: "https://images.unsplash.com/photo-1485095329183-d0797cdc5676?w=400&h=600&fit=crop",
    tags: ["thriller", "violent", "minimalist", "dark", "contemplative", "tense"],
    tagScores: { thrilling: 0.90, violent: 0.88, minimalist: 0.85, dark: 0.92, contemplative: 0.80 },
    description: "Violence and mayhem ensue after a hunter stumbles upon drug money.",
    color: "#8b7355"
  },
  {
    id: 15,
    title: "Spirited Away",
    year: 2001,
    director: "Hayao Miyazaki",
    poster: "https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=600&fit=crop",
    tags: ["whimsical", "surreal", "heartwarming", "vibrant", "imaginative", "uplifting"],
    tagScores: { whimsical: 0.98, surreal: 0.90, heartwarming: 0.88, vibrant: 0.95, uplifting: 0.85 },
    description: "A young girl enters a world of spirits and must work to free her parents.",
    color: "#98d8c8"
  },
  {
    id: 16,
    title: "There Will Be Blood",
    year: 2007,
    director: "Paul Thomas Anderson",
    poster: "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=400&h=600&fit=crop",
    tags: ["dark", "intense", "contemplative", "violent", "epic", "character-study"],
    tagScores: { dark: 0.95, intense: 0.92, contemplative: 0.85, violent: 0.80, drama: 0.90 },
    description: "A ruthless oil prospector's ambition leads to devastating consequences.",
    color: "#2c1810"
  },
  {
    id: 17,
    title: "Children of Men",
    year: 2006,
    director: "Alfonso Cuarón",
    poster: "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400&h=600&fit=crop",
    tags: ["dystopian", "dark", "intense", "action", "gritty", "thrilling"],
    tagScores: { dystopian: 0.95, dark: 0.90, intense: 0.92, action: 0.85, gritty: 0.88 },
    description: "In a future without children, a bureaucrat must protect humanity's last hope.",
    color: "#5c6d70"
  },
  {
    id: 18,
    title: "The Grand Illusion",
    year: 1937,
    director: "Jean Renoir",
    poster: "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=400&h=600&fit=crop",
    tags: ["classic", "war", "humanist", "contemplative", "political", "timeless"],
    tagScores: { contemplative: 0.88, political: 0.85, drama: 0.90, slowburn: 0.75 },
    description: "French POWs attempt escape during World War I.",
    color: "#8b8378"
  },
  {
    id: 19,
    title: "Oldboy",
    year: 2003,
    director: "Park Chan-wook",
    poster: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=400&h=600&fit=crop",
    tags: ["violent", "dark", "thrilling", "revenge", "intense", "stylish"],
    tagScores: { violent: 0.95, dark: 0.92, thrilling: 0.90, intense: 0.95, mystery: 0.85 },
    description: "After being kidnapped and imprisoned for 15 years, a man seeks revenge.",
    color: "#8b0000"
  },
  {
    id: 20,
    title: "The Shape of Water",
    year: 2017,
    director: "Guillermo del Toro",
    poster: "https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=400&h=600&fit=crop",
    tags: ["romantic", "whimsical", "vibrant", "surreal", "fantasy", "heartwarming"],
    tagScores: { romantic: 0.90, whimsical: 0.85, vibrant: 0.88, surreal: 0.82, heartwarming: 0.85 },
    description: "A mute woman falls in love with an amphibious creature.",
    color: "#1e847f"
  },
  {
    id: 21,
    title: "In the Mood for Love",
    year: 2000,
    director: "Wong Kar-wai",
    poster: "https://images.unsplash.com/photo-1518929458119-e5bf444c30f4?w=400&h=600&fit=crop",
    tags: ["romantic", "melancholic", "stylish", "slowburn", "contemplative", "vibrant"],
    tagScores: { romantic: 0.95, melancholic: 0.92, slowburn: 0.90, contemplative: 0.88, vibrant: 0.80 },
    description: "Two neighbors form a bond after suspecting their spouses of infidelity.",
    color: "#d4145a"
  },
  {
    id: 22,
    title: "Whiplash",
    year: 2014,
    director: "Damien Chazelle",
    poster: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=600&fit=crop",
    tags: ["intense", "thrilling", "dark", "fastpaced", "character-study", "visceral"],
    tagScores: { intense: 0.98, thrilling: 0.92, dark: 0.85, fastpaced: 0.88, drama: 0.90 },
    description: "A young drummer's pursuit of perfection under an abusive instructor.",
    color: "#ffd700"
  },
  {
    id: 23,
    title: "Pan's Labyrinth",
    year: 2006,
    director: "Guillermo del Toro",
    poster: "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=400&h=600&fit=crop",
    tags: ["dark", "fantasy", "violent", "surreal", "melancholic", "visually stunning"],
    tagScores: { dark: 0.90, violent: 0.85, surreal: 0.92, melancholic: 0.85, vibrant: 0.78 },
    description: "A young girl escapes into a mythical labyrinth during Spanish Civil War.",
    color: "#2d4654"
  },
  {
    id: 24,
    title: "Goodfellas",
    year: 1990,
    director: "Martin Scorsese",
    poster: "https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop",
    tags: ["crime", "violent", "fastpaced", "stylish", "intense", "dark"],
    tagScores: { violent: 0.88, fastpaced: 0.92, dark: 0.85, intense: 0.88, drama: 0.85 },
    description: "The story of Henry Hill and his life in the mob.",
    color: "#8b0000"
  },
  {
    id: 25,
    title: "2001: A Space Odyssey",
    year: 1968,
    director: "Stanley Kubrick",
    poster: "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=600&fit=crop",
    tags: ["scifi", "philosophical", "slowburn", "contemplative", "surreal", "visually stunning"],
    tagScores: { scifi: 0.98, philosophical: 0.95, slowburn: 0.95, contemplative: 0.92, surreal: 0.88 },
    description: "Humanity's journey from apes to space exploration and beyond.",
    color: "#000000"
  },
  {
    id: 26,
    title: "La La Land",
    year: 2016,
    director: "Damien Chazelle",
    poster: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop",
    tags: ["romantic", "vibrant", "musical", "melancholic", "whimsical", "uplifting"],
    tagScores: { romantic: 0.92, vibrant: 0.95, melancholic: 0.78, whimsical: 0.85, uplifting: 0.80 },
    description: "An aspiring actress and a jazz musician fall in love in Los Angeles.",
    color: "#6c5ce7"
  },
  {
    id: 27,
    title: "The Lighthouse",
    year: 2019,
    director: "Robert Eggers",
    poster: "https://images.unsplash.com/photo-1495954484750-af469f2f9be5?w=400&h=600&fit=crop",
    tags: ["dark", "surreal", "intense", "psychological", "atmospheric", "horror"],
    tagScores: { dark: 0.98, surreal: 0.92, intense: 0.95, horror: 0.85, atmospheric: 0.90 },
    description: "Two lighthouse keepers descend into madness on a remote island.",
    color: "#1a1a1a"
  },
  {
    id: 28,
    title: "City of God",
    year: 2002,
    director: "Fernando Meirelles",
    poster: "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=400&h=600&fit=crop",
    tags: ["gritty", "violent", "intense", "vibrant", "fastpaced", "political"],
    tagScores: { gritty: 0.95, violent: 0.92, intense: 0.90, vibrant: 0.85, fastpaced: 0.88, political: 0.80 },
    description: "The story of organized crime in the favelas of Rio de Janeiro.",
    color: "#ffa500"
  },
  {
    id: 29,
    title: "A Clockwork Orange",
    year: 1971,
    director: "Stanley Kubrick",
    poster: "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400&h=600&fit=crop",
    tags: ["dystopian", "violent", "surreal", "dark", "philosophical", "stylish"],
    tagScores: { dystopian: 0.92, violent: 0.95, surreal: 0.88, dark: 0.90, philosophical: 0.85, stylish: 0.88 },
    description: "A violent delinquent undergoes experimental behavior modification.",
    color: "#ff6348"
  },
  {
    id: 30,
    title: "The Handmaiden",
    year: 2016,
    director: "Park Chan-wook",
    poster: "https://images.unsplash.com/photo-1518929458119-e5bf444c30f4?w=400&h=600&fit=crop",
    tags: ["thriller", "romantic", "stylish", "twisty", "vibrant", "erotic"],
    tagScores: { thrilling: 0.88, romantic: 0.85, vibrant: 0.90, mystery: 0.85, stylish: 0.92 },
    description: "A con-man and a young woman develop an unexpected relationship.",
    color: "#e056fd"
  },
  {
    id: 31,
    title: "Everything Everywhere All at Once",
    year: 2022,
    director: "Daniels",
    poster: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&h=600&fit=crop",
    tags: ["surreal", "action", "comedic", "philosophical", "vibrant", "heartwarming"],
    tagScores: { surreal: 0.98, action: 0.88, comedic: 0.85, philosophical: 0.82, vibrant: 0.95, heartwarming: 0.85 },
    description: "A woman must navigate the multiverse to save reality.",
    color: "#ff00ff"
  },
  {
    id: 32,
    title: "Arrival",
    year: 2016,
    director: "Denis Villeneuve",
    poster: "https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=400&h=600&fit=crop",
    tags: ["scifi", "philosophical", "contemplative", "minimalist", "slowburn", "emotional"],
    tagScores: { scifi: 0.90, philosophical: 0.92, contemplative: 0.95, minimalist: 0.85, slowburn: 0.88 },
    description: "A linguist works with the military to communicate with aliens.",
    color: "#2c3e50"
  },
  {
    id: 33,
    title: "The Killing of a Sacred Deer",
    year: 2017,
    director: "Yorgos Lanthimos",
    poster: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=400&h=600&fit=crop",
    tags: ["dark", "surreal", "disturbing", "minimalist", "psychological", "slowburn"],
    tagScores: { dark: 0.95, surreal: 0.88, minimalist: 0.90, intense: 0.85, slowburn: 0.82 },
    description: "A surgeon must make an impossible choice after a mysterious tragedy.",
    color: "#34495e"
  },
  {
    id: 34,
    title: "Lost in Translation",
    year: 2003,
    director: "Sofia Coppola",
    poster: "https://images.unsplash.com/photo-1492619392994-8a3a63a5ff0f?w=400&h=600&fit=crop",
    tags: ["melancholic", "romantic", "contemplative", "minimalist", "intimate", "atmospheric"],
    tagScores: { melancholic: 0.90, romantic: 0.82, contemplative: 0.88, minimalist: 0.85, intimate: 0.90 },
    description: "Two lost souls find connection in Tokyo.",
    color: "#ff69b4"
  },
  {
    id: 35,
    title: "The Prestige",
    year: 2006,
    director: "Christopher Nolan",
    poster: "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400&h=600&fit=crop",
    tags: ["mystery", "thriller", "dark", "twisty", "period", "obsessive"],
    tagScores: { mystery: 0.95, thrilling: 0.90, dark: 0.85, drama: 0.88 },
    description: "Two magicians engage in a bitter rivalry.",
    color: "#1e272e"
  },
  {
    id: 36,
    title: "Hereditary",
    year: 2018,
    director: "Ari Aster",
    poster: "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400&h=600&fit=crop",
    tags: ["horror", "dark", "intense", "disturbing", "atmospheric", "slowburn"],
    tagScores: { horror: 0.95, dark: 0.98, intense: 0.92, atmospheric: 0.90, slowburn: 0.85 },
    description: "A family is haunted by a mysterious presence after their matriarch's death.",
    color: "#2d3436"
  },
  {
    id: 37,
    title: "The Social Network",
    year: 2010,
    director: "David Fincher",
    poster: "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400&h=600&fit=crop",
    tags: ["fastpaced", "dialogue-driven", "contemporary", "dark", "character-study"],
    tagScores: { fastpaced: 0.88, dark: 0.78, drama: 0.90, intense: 0.80 },
    description: "The founding of Facebook and the lawsuits that followed.",
    color: "#3b5998"
  },
  {
    id: 38,
    title: "Portrait of a Lady on Fire",
    year: 2019,
    director: "Céline Sciamma",
    poster: "https://images.unsplash.com/photo-1518929458119-e5bf444c30f4?w=400&h=600&fit=crop",
    tags: ["romantic", "contemplative", "slowburn", "intimate", "period", "melancholic"],
    tagScores: { romantic: 0.95, contemplative: 0.92, slowburn: 0.90, intimate: 0.95, melancholic: 0.85 },
    description: "An artist falls in love with her subject in 18th century France.",
    color: "#d63031"
  },
  {
    id: 39,
    title: "Hot Fuzz",
    year: 2007,
    director: "Edgar Wright",
    poster: "https://images.unsplash.com/photo-1594908900066-3f47337549d8?w=400&h=600&fit=crop",
    tags: ["comedic", "action", "satire", "fastpaced", "quirky", "uplifting"],
    tagScores: { comedic: 0.95, action: 0.88, fastpaced: 0.92, quirky: 0.85, uplifting: 0.80 },
    description: "A top London cop struggles to adapt to his quiet new village.",
    color: "#e74c3c"
  },
  {
    id: 40,
    title: "Memories of Murder",
    year: 2003,
    director: "Bong Joon-ho",
    poster: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=400&h=600&fit=crop",
    tags: ["mystery", "dark", "atmospheric", "slowburn", "thriller", "melancholic"],
    tagScores: { mystery: 0.95, dark: 0.90, atmospheric: 0.92, slowburn: 0.88, thrilling: 0.85, melancholic: 0.80 },
    description: "Detectives investigate a series of murders in rural South Korea.",
    color: "#636e72"
  },
  {
    id: 41,
    title: "Fantastic Mr. Fox",
    year: 2009,
    director: "Wes Anderson",
    poster: "https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=600&fit=crop",
    tags: ["whimsical", "comedic", "vibrant", "quirky", "heartwarming", "stylish"],
    tagScores: { whimsical: 0.95, comedic: 0.88, vibrant: 0.92, quirky: 0.90, heartwarming: 0.85, stylish: 0.88 },
    description: "An anthropomorphic fox battles three mean farmers.",
    color: "#f39c12"
  },
  {
    id: 42,
    title: "Uncut Gems",
    year: 2019,
    director: "Safdie Brothers",
    poster: "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=400&h=600&fit=crop",
    tags: ["intense", "fastpaced", "thriller", "stressful", "gritty", "chaotic"],
    tagScores: { intense: 0.98, fastpaced: 0.95, thrilling: 0.92, gritty: 0.88 },
    description: "A jeweler makes a high-stakes bet that could lead to his destruction.",
    color: "#9b59b6"
  },
  {
    id: 43,
    title: "The Lobster",
    year: 2015,
    director: "Yorgos Lanthimos",
    poster: "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=400&h=600&fit=crop",
    tags: ["surreal", "dark", "quirky", "dystopian", "satirical", "deadpan"],
    tagScores: { surreal: 0.95, dark: 0.88, quirky: 0.92, dystopian: 0.85, comedic: 0.70 },
    description: "Single people must find a mate in 45 days or be transformed into animals.",
    color: "#e17055"
  },
  {
    id: 44,
    title: "The Witch",
    year: 2015,
    director: "Robert Eggers",
    poster: "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400&h=600&fit=crop",
    tags: ["horror", "dark", "atmospheric", "period", "slowburn", "unsettling"],
    tagScores: { horror: 0.90, dark: 0.95, atmospheric: 0.95, slowburn: 0.88 },
    description: "A Puritan family encounters evil forces in 1630s New England.",
    color: "#2d3436"
  },
  {
    id: 45,
    title: "Knives Out",
    year: 2019,
    director: "Rian Johnson",
    poster: "https://images.unsplash.com/photo-1571847140471-1d7766e825ea?w=400&h=600&fit=crop",
    tags: ["mystery", "comedic", "clever", "ensemble", "twisty", "uplifting"],
    tagScores: { mystery: 0.92, comedic: 0.85, fastpaced: 0.80, uplifting: 0.75 },
    description: "A detective investigates the death of a patriarch of an eccentric family.",
    color: "#f39c12"
  }
];

// Helper function to get random subset of movies for quiz
export function getRandomMovies(count: number): Movie[] {
  const shuffled = [...MOVIES].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

// Get a random number of questions (5-10)
export function getRandomQuestionCount(): number {
  return Math.floor(Math.random() * 6) + 5; // 5-10
}
