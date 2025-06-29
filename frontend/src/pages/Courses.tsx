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
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
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

  useEffect(() => {
    let filtered = allCourses;

    if (searchTerm) {
      filtered = filtered.filter(course =>
        (course.title?.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (course.description?.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (Array.isArray(course.skills) && course.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase())))
      );
    }

    if (selectedLevel !== 'all') {
      filtered = filtered.filter(course => course.level === selectedLevel);
    }

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(course => course.category === selectedCategory);
    }

    setFilteredCourses(filtered);
  }, [searchTerm, selectedLevel, selectedCategory, allCourses]);

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
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search Courses</label>
              <Search className="absolute left-3 bottom-2.5 h-4 w-4 text-gray-400" />
              <Input
                id="search"
                placeholder="e.g., Python, Data Science"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
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
            <CourseGrid courses={paginatedExternal} onCourseClick={() => {}} />
            <PaginationControls
              currentPage={externalPage}
              totalPages={totalExternalPages}
              onPageChange={setExternalPage}
              siblingCount={1}
            />
          </TabsContent>
          <TabsContent value="internal" className="mt-4">
            <CourseGrid courses={paginatedInternal} onCourseClick={handleCourseClick} />
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

const CourseGrid = ({ courses, onCourseClick }: { courses: Course[], onCourseClick: (course: Course) => void }) => {
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
        <CourseCard key={course.id} course={course} onCourseClick={onCourseClick} />
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

const CourseCard: React.FC<{ course: Course; onCourseClick: (course: Course) => void }> = ({ course, onCourseClick }) => {
  const handleCardClick = () => {
    if (!course.isExternal) {
      onCourseClick(course);
    }
  };

  return (
    <Card 
      onClick={handleCardClick}
      className={`hover:shadow-lg transition-all duration-200 group flex flex-col ${!course.isExternal ? 'cursor-pointer' : ''}`}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 mr-2">
            <div className="flex items-center space-x-2 mb-2">
              {course.isExternal ? (
                <ExternalLink className="h-4 w-4 text-green-600" />
              ) : (
                <GraduationCap className="h-4 w-4 text-blue-600" />
              )}
              <Badge variant={course.isExternal ? "default" : "secondary"}>
                {course.provider}
              </Badge>
            </div>
            <CardTitle className="text-base font-bold leading-snug group-hover:text-blue-600 transition-colors">
              {course.title}
            </CardTitle>
          </div>
          {course.level && <Badge variant="outline" className="flex-shrink-0">{course.level}</Badge>}
        </div>
        <CardDescription className="line-clamp-2 text-sm mt-2">
          {course.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col justify-end">
        {Array.isArray(course.skills) && course.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {course.skills.slice(0, 3).map((skill, index) => (
              <Badge key={index} variant="outline" className="text-xs font-normal">
                {skill}
              </Badge>
            ))}
            {course.skills.length > 3 && (
              <Badge variant="outline" className="text-xs font-normal">
                +{course.skills.length - 3} more
              </Badge>
            )}
          </div>
        )}
        <div className="border-t pt-3 mt-auto">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-3">
              {course.video_count && (
                <div className="flex items-center gap-1">
                  <ListVideo className="h-3 w-3" />
                  <span>{course.video_count} videos</span>
                </div>
              )}
              {course.duration && (
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>{course.duration}</span>
                </div>
              )}
              {course.rating != null && (
                <div className="flex items-center gap-1">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  <span>{course.rating.toFixed(1)}</span>
                </div>
              )}
              {course.num_reviews != null && (
                <div className="flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  <span>{course.num_reviews.toLocaleString()}</span>
                </div>
              )}
            </div>
            <div className="flex items-center">
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <ThumbsUp className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <ThumbsDown className="h-4 w-4" />
              </Button>
            </div>
          </div>
          {course.isExternal && course.url && (
            <Button
              asChild
              className="w-full mt-3 bg-green-600 hover:bg-green-700"
            >
              <a 
                href={course.url} 
                target="_blank" 
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View on Provider
              </a>
            </Button>
          )}
          {!course.isExternal && (
            <Button
              onClick={(e) => {
                  e.stopPropagation();
                  onCourseClick(course);
              }}
              className="w-full mt-3 bg-blue-600 hover:bg-blue-700"
            >
              <PlayCircle className="h-4 w-4 mr-2" />
              View Playlist
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default Courses; 