import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Heart, Clock, Star, ExternalLink, ThumbsDown } from 'lucide-react';
import { toast } from 'sonner';

// Adjusted Course type to be more flexible
export interface Course {
  id: number | string;
  item_id: string;
  title: string;
  description?: string | null;
  provider?: string | null;
  url: string;
  level?: string | null;
  skills?: string[] | string | null;
  duration?: number | null;
  rating?: number | null;
}

interface CourseCardProps {
  course: Course;
  onLike?: (courseId: string) => void;
  onDislike?: (courseId: string) => void;
}

// Helper to safely get properties
const getSafe = <T, K extends keyof T>(obj: T, key: K, defaultValue: any = ''): any => {
    return obj && typeof obj === 'object' && key in obj ? obj[key] : defaultValue;
};

// Helper function to log interactions
const logInteraction = async (courseId: string, interactionType: string, value?: number) => {
  try {
    const token = localStorage.getItem('novalearn_token');
    if (!token) return; // Don't log if user is not authenticated

    await fetch('http://localhost:8000/interactions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ 
        course_id: courseId, 
        interaction_type: interactionType,
        value: value 
      }),
    });
  } catch (error) {
    console.error('Failed to log interaction:', error);
  }
};

const CourseCard: React.FC<CourseCardProps> = ({ course, onLike, onDislike }) => {
  const navigate = useNavigate();
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  if (!course || !course.item_id) {
    console.error("CourseCard received an invalid course object:", course);
    return (
        <div className="border rounded-lg p-4 text-red-500">
            Invalid course data provided.
        </div>
    );
  }

  const title = getSafe(course, 'title', 'No Title');
  const description = getSafe(course, 'description', 'No description available.');
  const provider = getSafe(course, 'provider');
  const level = getSafe(course, 'level');
  const rating = getSafe(course, 'rating', 0);
  const duration = getSafe(course, 'duration');
  
  // Safely handle skills, which could be an array or a comma-separated string
  let skills: string[] = [];
  const rawSkills = getSafe(course, 'skills');
  if (Array.isArray(rawSkills)) {
    skills = rawSkills;
  } else if (typeof rawSkills === 'string' && rawSkills.length > 0) {
    skills = rawSkills.split(',').map(s => s.trim());
  }

  // Determine the correct ID to use for navigation and actions
  const courseId = course.id || course.item_id;
  const isExternal = course.course_type === 'external';

  const handleMouseEnter = () => {
    // Log hover after 3 seconds of hovering (increased from 2 seconds)
    hoverTimeoutRef.current = setTimeout(() => {
      if (courseId) {
        logInteraction(String(courseId), 'hover');
      }
    }, 3000); // Increased to 3 seconds for more meaningful interaction
  };

  const handleMouseLeave = () => {
    // Clear hover timeout if mouse leaves before 3 seconds
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
  };

  const handleCardClick = () => {
    // Log click interaction
    if (courseId) {
      logInteraction(String(courseId), 'click');
    }

    if (isExternal && course.url) {
      window.open(course.url, '_blank', 'noopener,noreferrer');
    } else if (course.playlist_title) {
      navigate(`/playlist/${encodeURIComponent(course.playlist_title)}`);
    }
  };
  
  const handleLikeClick = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when liking
    if (courseId) {
      // Use custom onLike callback if provided, otherwise use default API call
      if (onLike) {
        onLike(String(courseId));
      } else {
        try {
          const token = localStorage.getItem('novalearn_token');
          if (!token) {
            toast.error("You must be logged in to like a course.");
            return;
          }
          const response = await fetch('http://localhost:8000/interactions', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ course_id: String(courseId), interaction_type: 'like' }),
          });
          if (!response.ok) {
            throw new Error("Failed to save like.");
          }
          toast.success("Thanks for your feedback!");
        } catch (error: any) {
          toast.error(error.message || "Could not save feedback.");
        }
      }
    }
  };

  const handleDislikeClick = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click when disliking
    if (courseId) {
      // Use custom onDislike callback if provided, otherwise use default API call
      if (onDislike) {
        onDislike(String(courseId));
      } else {
        try {
          const token = localStorage.getItem('novalearn_token');
          if (!token) {
            toast.error("You must be logged in to dislike a course.");
            return;
          }
          const response = await fetch('http://localhost:8000/interactions', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ course_id: String(courseId), interaction_type: 'dislike' }),
          });
          if (!response.ok) {
            throw new Error("Failed to save dislike.");
          }
          toast.success("Feedback saved!");
        } catch (error: any) {
          toast.error(error.message || "Could not save feedback.");
        }
      }
    }
  };

  const skillsToDisplay = skills.slice(0, 4);

  return (
    <Card 
      className="hover:shadow-lg transition-shadow cursor-pointer flex flex-col"
      onClick={handleCardClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg flex-grow pr-2">{title || course.playlist_title}</CardTitle>
          <div className="flex gap-1 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLikeClick}
              className="text-gray-400 hover:text-red-500"
              aria-label="Like course"
            >
              <Heart className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDislikeClick}
              className="text-gray-400 hover:text-gray-600"
              aria-label="Dislike course"
            >
              <ThumbsDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <CardDescription className="line-clamp-2">{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex-grow flex flex-col justify-between">
        <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
                <Badge variant="secondary">{provider}</Badge>
                <Badge variant="outline">{level || 'All Levels'}</Badge>
            </div>

            <div className="flex flex-wrap gap-1 min-h-[22px]">
                {skillsToDisplay.map((skill: string, index: number) => (
                <Badge key={`${skill}-${index}`} variant="outline" className="text-xs font-normal">
                    {skill}
                </Badge>
                ))}
            </div>
        </div>

        <div className="flex items-center justify-between pt-4 mt-auto">
            <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                <span>{duration ? `${duration} hrs` : 'N/A'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>{rating ? rating.toFixed(1) : 'N/A'}</span>
                </div>
            </div>
            {isExternal && (
                <ExternalLink className="h-5 w-5 text-blue-500" />
            )}
        </div>
      </CardContent>
    </Card>
  );
};

export default CourseCard; 