import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BookOpen, Clock, Star, ExternalLink, Search, Users, GraduationCap, ChevronLeft, ChevronRight, ThumbsUp, ThumbsDown, ListVideo, PlayCircle } from 'lucide-react';
import CourseCard, { Course as SharedCourse } from '../components/shared/CourseCard';
import { toast } from 'sonner';

interface Course {
  id: string;
  title: string;
  description: string;
  provider: string;
  level: string;
  duration?: string;
  skills: string[];
  isExternal: boolean;
  category?: string;
  url?: string;
  rating?: number;
  num_reviews?: number;
  playlist_title?: string;
  video_count?: number;
}

const Courses = () => {
  const navigate = useNavigate();
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [searchResults, setSearchResults] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [internalPage, setInternalPage] = useState(1);
  const [externalPage, setExternalPage] = useState(1);
  
  const ITEMS_PER_PAGE = 9;

  const capitalizeWords = (str: string | null): string | null => {
    if (!str) return null;
    return str
      .toLowerCase()
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Function to search courses using the API
  const searchCourses = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const token = localStorage.getItem('novalearn_token');
      const headers: any = {
        'Content-Type': 'application/json',
      };
      
      // Add auth header if user is logged in (for interaction logging)
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://localhost:8000/search/all?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error('Failed to search courses');
      }

      const apiResults = await response.json();
      
      // Transform API results to match our Course interface
      const transformedResults: Course[] = apiResults.map((c: any) => {
        const isExternal = c.course_type === 'external';
        const skills = Array.isArray(c.skills) ? c.skills : [];
        
        return {
          id: c.id,
          title: c.title || 'Untitled Course',
          description: c.description || 'No description available',
          provider: c.provider || (isExternal ? 'Unknown' : 'University'),
          level: isExternal ? (capitalizeWords(c.level) || 'All Levels') : 'University Level',
          duration: c.duration ? `${c.duration} hours` : undefined,
          skills: skills,
          isExternal: isExternal,
          rating: c.rating || 0,
          category: skills.length > 0 ? skills[0] : (isExternal ? 'General' : 'University'),
          url: c.url || '',
          playlist_title: isExternal ? undefined : c.title,
        };
      });

      setSearchResults(transformedResults);
      console.log(`🔍 Search completed: Found ${transformedResults.length} results for "${query}"`);
    } catch (error) {
      console.error("Failed to search courses:", error);
      toast.error("Failed to search courses. Please try again.");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm.trim()) {
        searchCourses(searchTerm);
      } else {
        setSearchResults([]);
        setIsSearching(false);
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  useEffect(() => {
    const fetchAllCourses = async () => {
      setLoading(true);
      setError(null);
      try {
        const [internalRes, externalRes] = await Promise.all([
          fetch('http://localhost:8000/courses/internal?limit=20000'),
          fetch('http://localhost:8000/courses/external?limit=20000')
        ]);

        if (!internalRes.ok || !externalRes.ok) {
          throw new Error('Failed to fetch courses');
        }

        const internalData = await internalRes.json();
        const externalData = await externalRes.json();

        // Group internal videos by playlist
        const playlists: { [key: string]: any[] } = internalData.reduce((acc: { [key: string]: any[] }, video: any) => {
          const playlistTitle = video.playlist_title || "Uncategorized";
          if (!acc[playlistTitle]) {
            acc[playlistTitle] = [];
          }
          acc[playlistTitle].push(video);
          return acc;
        }, {});

        const transformedInternal: Course[] = Object.keys(playlists).map(playlistTitle => {
          const videos = playlists[playlistTitle];
          const firstVideo = videos[0];
          return {
            id: encodeURIComponent(playlistTitle),
            title: playlistTitle,
            description: `A playlist with ${videos.length} videos on topics related to ${playlistTitle}.`,
            provider: 'University',
            level: 'University Level',
            skills: [],
            isExternal: false,
            url: firstVideo.playlist_url,
            playlist_title: playlistTitle,
            category: 'University',
            video_count: videos.length,
          };
        });

        const transformedExternal: Course[] = externalData.map((c: any) => ({
          id: c.item_id,
          title: c.title,
          description: c.description,
          provider: c.provider,
          level: capitalizeWords(c.level),
          duration: c.duration ? `${c.duration} hours` : undefined,
          skills: c.skills || [],
          isExternal: true,
          rating: c.rating,
          num_reviews: c.num_reviews,
          category: Array.isArray(c.skills) && c.skills.length > 0 ? c.skills[0] : 'General',
          url: c.url,
        }));

        const combinedCourses = [...transformedInternal, ...transformedExternal];
        setAllCourses(combinedCourses);
        setFilteredCourses(combinedCourses);
      } catch (error) {
        console.error("Failed to fetch courses:", error);
        setError("Failed to load courses. Please make sure the backend is running and refresh the page.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllCourses();
  }, []);

  // Filter courses based on search results or all courses
  useEffect(() => {
    // Use search results if searching, otherwise use all courses
    const coursesToFilter = searchTerm.trim() ? searchResults : allCourses;
    let filtered = coursesToFilter;

    // Apply level filter
    if (selectedLevel !== 'all') {
      filtered = filtered.filter(course => course.level === selectedLevel);
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(course => course.category === selectedCategory);
    }

    setFilteredCourses(filtered);
    
    // Reset pagination when filters change
    setInternalPage(1);
    setExternalPage(1);
  }, [searchResults, allCourses, selectedLevel, selectedCategory, searchTerm]);

  const handleCourseClick = (course: Course) => {
    if (course.isExternal) {
       // External courses are handled by the action button
       return;
    } else {
        navigate(`/playlist/${course.id}`);
    }
  };

  const internalCourses = filteredCourses.filter(course => !course.isExternal);
  const externalCourses = filteredCourses.filter(course => course.isExternal);

  const paginatedInternal = internalCourses.slice((internalPage - 1) * ITEMS_PER_PAGE, internalPage * ITEMS_PER_PAGE);
  const paginatedExternal = externalCourses.slice((externalPage - 1) * ITEMS_PER_PAGE, externalPage * ITEMS_PER_PAGE);
  const totalInternalPages = Math.ceil(internalCourses.length / ITEMS_PER_PAGE);
  const totalExternalPages = Math.ceil(externalCourses.length / ITEMS_PER_PAGE);

  const categories = ['all', ...Array.from(new Set(allCourses.map(course => course.category).filter(Boolean)))];
  const levels = ['all', ...Array.from(new Set(allCourses.map(course => course.level).filter(Boolean)))];

  // Transform Course to SharedCourse for the CourseCard component
  const transformToSharedCourse = (course: Course): SharedCourse => ({
    id: course.id,
    item_id: course.id,
    title: course.title,
    description: course.description,
    provider: course.provider,
    url: course.url || '',
    level: course.level,
    skills: course.skills,
    duration: course.duration ? parseInt(course.duration.split(' ')[0]) || 0 : 0,
    rating: course.rating,
    course_type: course.isExternal ? 'external' : 'internal',
    playlist_title: course.playlist_title,
  });

  const handleLike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to like a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'like' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save like.");
      }
      toast.success("Thanks for your feedback!");
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

  const handleDislike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to dislike a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'dislike' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save dislike.");
      }
      toast.success("Feedback saved!");
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="text-red-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-800">Something went wrong</h2>
          <p className="text-gray-600 mt-2">{error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 p-4 sm:p-6 lg:p-8">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
          <div className="flex items-center space-x-3 mb-4">
            <BookOpen className="h-8 w-8" />
            <h1 className="text-3xl font-bold">Course Catalog</h1>
          </div>
          <p className="text-blue-100">Explore our comprehensive catalog of internal and external courses.</p>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{allCourses.length.toLocaleString()}</div>
              <div className="text-blue-200">Total Courses</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{internalCourses.length.toLocaleString()}</div>
              <div className="text-blue-200">University Courses</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{externalCourses.length.toLocaleString()}</div>
              <div className="text-blue-200">External Recommendations</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div className="relative col-span-1 md:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                Search Courses
                {isSearching && (
                  <span className="ml-2 text-xs text-blue-600 inline-flex items-center">
                    <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-600 mr-1"></div>
                    Searching...
                  </span>
                )}
              </label>
              <Search className="absolute left-3 bottom-2.5 h-4 w-4 text-gray-400" />
              <Input
                id="search"
                placeholder="e.g., Python, Data Science, Machine Learning"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              {searchTerm && (
                <div className="mt-2 text-xs text-gray-600">
                  {isSearching ? (
                    "Searching database..."
                  ) : searchResults.length > 0 ? (
                    `Found ${searchResults.length} results for "${searchTerm}"`
                  ) : searchTerm.trim() ? (
                    `No results found for "${searchTerm}"`
                  ) : null}
                </div>
              )}
            </div>
            <div>
              <label htmlFor="level" className="block text-sm font-medium text-gray-700 mb-1">Filter by Level</label>
              <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                <SelectTrigger id="level">
                  <SelectValue placeholder="All Levels" />
                </SelectTrigger>
                <SelectContent>
                  {levels.map(level => (
                    <SelectItem key={level} value={level}>
                      {level === 'all' ? 'All Levels' : level}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
             <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">Filter by Category</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger id="category">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category === 'all' ? 'All Categories' : category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <Tabs defaultValue="external" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="external">External Courses ({externalCourses.length.toLocaleString()})</TabsTrigger>
            <TabsTrigger value="internal">University Courses ({internalCourses.length.toLocaleString()})</TabsTrigger>
          </TabsList>
          <TabsContent value="external" className="mt-4">
            <CourseGrid 
              courses={paginatedExternal} 
              onCourseClick={() => {}}
              transformToSharedCourse={transformToSharedCourse}
              handleLike={handleLike}
              handleDislike={handleDislike}
            />
            <PaginationControls
              currentPage={externalPage}
              totalPages={totalExternalPages}
              onPageChange={setExternalPage}
              siblingCount={1}
            />
          </TabsContent>
          <TabsContent value="internal" className="mt-4">
            <CourseGrid 
              courses={paginatedInternal} 
              onCourseClick={handleCourseClick}
              transformToSharedCourse={transformToSharedCourse}
              handleLike={handleLike}
              handleDislike={handleDislike}
            />
             <PaginationControls
              currentPage={internalPage}
              totalPages={totalInternalPages}
              onPageChange={setInternalPage}
              siblingCount={1}
            />
          </TabsContent>
        </Tabs>
        
        {filteredCourses.length === 0 && !loading && (
          <div className="text-center py-12 bg-gray-50 rounded-lg mt-6">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">No Courses Found</h3>
            <p className="text-gray-500">Try adjusting your filters to see all available courses.</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

const CourseGrid = ({ 
  courses, 
  onCourseClick, 
  transformToSharedCourse, 
  handleLike, 
  handleDislike 
}: { 
  courses: Course[], 
  onCourseClick: (course: Course) => void,
  transformToSharedCourse: (course: Course) => SharedCourse,
  handleLike: (courseId: string) => void,
  handleDislike: (courseId: string) => void
}) => {
  if (courses.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <BookOpen className="h-10 w-10 mx-auto mb-2" />
        <p>No courses match the current filters.</p>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {courses.map((course) => (
        <CourseCard 
          key={course.id} 
          course={transformToSharedCourse(course)} 
          onLike={() => handleLike(course.id)}
          onDislike={() => handleDislike(course.id)}
        />
      ))}
    </div>
  );
};

const PaginationControls = ({ currentPage, totalPages, onPageChange }: { currentPage: number, totalPages: number, onPageChange: (page: number) => void, siblingCount?: number }) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center space-x-2 mt-8">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        <ChevronLeft className="h-4 w-4 mr-1" />
        Previous
      </Button>
      <span className="text-sm text-gray-600">
        Page {currentPage} of {totalPages.toLocaleString()}
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        Next
        <ChevronRight className="h-4 w-4 ml-1" />
      </Button>
    </div>
  );
};

export default Courses; 