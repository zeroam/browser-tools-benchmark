import React from "react";

export interface CalendarEvent {
  id: number;
  title: string;
  startTime: string;
  endTime: string;
  day: string;
  color: string;
}

export const calendarEvents: CalendarEvent[] = [
  {
    id: 1,
    title: "Team Meeting",
    startTime: "09:00",
    endTime: "10:30",
    day: "Monday",
    color: "bg-blue-100",
  },
  {
    id: 2,
    title: "Lunch with Client",
    startTime: "12:00",
    endTime: "13:30",
    day: "Tuesday",
    color: "bg-purple-100",
  },
  {
    id: 3,
    title: "Project Review",
    startTime: "14:00",
    endTime: "15:00",
    day: "Wednesday",
    color: "bg-green-100",
  },
  {
    id: 4,
    title: "Training Session",
    startTime: "11:00",
    endTime: "12:30",
    day: "Thursday",
    color: "bg-orange-100",
  },
  {
    id: 5,
    title: "Weekly Sync",
    startTime: "15:30",
    endTime: "16:30",
    day: "Friday",
    color: "bg-sky-100",
  },
  {
    id: 6,
    title: "Code Review",
    startTime: "10:30",
    endTime: "11:30",
    day: "Monday",
    color: "bg-yellow-100",
  },
  {
    id: 7,
    title: "Design Workshop",
    startTime: "13:00",
    endTime: "14:30",
    day: "Monday",
    color: "bg-pink-100",
  },
  {
    id: 8,
    title: "Client Call",
    startTime: "15:00",
    endTime: "16:00",
    day: "Monday",
    color: "bg-indigo-100",
  },
  {
    id: 9,
    title: "Sprint Planning",
    startTime: "09:30",
    endTime: "11:00",
    day: "Tuesday",
    color: "bg-emerald-100",
  },
  {
    id: 10,
    title: "Team Building",
    startTime: "14:00",
    endTime: "17:00",
    day: "Tuesday",
    color: "bg-cyan-100",
  },
  {
    id: 11,
    title: "Bug Triage",
    startTime: "09:00",
    endTime: "10:00",
    day: "Wednesday",
    color: "bg-violet-100",
  },
  {
    id: 12,
    title: "Stakeholder Update",
    startTime: "11:30",
    endTime: "12:30",
    day: "Wednesday",
    color: "bg-rose-100",
  },
  {
    id: 13,
    title: "Product Demo",
    startTime: "16:00",
    endTime: "17:00",
    day: "Wednesday",
    color: "bg-amber-100",
  },
  {
    id: 14,
    title: "1:1 with Manager",
    startTime: "09:30",
    endTime: "10:00",
    day: "Thursday",
    color: "bg-lime-100",
  },
  {
    id: 15,
    title: "Tech Talk",
    startTime: "13:00",
    endTime: "14:00",
    day: "Thursday",
    color: "bg-teal-100",
  },
  {
    id: 16,
    title: "Architecture Review",
    startTime: "15:00",
    endTime: "16:30",
    day: "Thursday",
    color: "bg-fuchsia-100",
  },
  {
    id: 17,
    title: "Stand-up",
    startTime: "09:00",
    endTime: "09:30",
    day: "Friday",
    color: "bg-blue-100",
  },
  {
    id: 18,
    title: "Documentation",
    startTime: "10:00",
    endTime: "12:00",
    day: "Friday",
    color: "bg-purple-100",
  },
  {
    id: 19,
    title: "Retrospective",
    startTime: "13:00",
    endTime: "14:30",
    day: "Friday",
    color: "bg-green-100",
  },
];

interface WeeklyCalendarProps {
  events: CalendarEvent[];
  days?: string[];
  startHour?: number;
  endHour?: number;
}

const WeeklyCalendar: React.FC<WeeklyCalendarProps> = ({
  events,
  days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  startHour = 9,
  endHour = 17,
}) => {
  const hours = Array.from(
    { length: endHour - startHour },
    (_, i) => `${i + startHour}:00`
  );

  const getEventPosition = (event: CalendarEvent) => {
    const startHour = parseInt(event.startTime.split(":")[0]);
    const startMinute = parseInt(event.startTime.split(":")[1]);
    const endHour = parseInt(event.endTime.split(":")[0]);
    const endMinute = parseInt(event.endTime.split(":")[1]);

    const startPercentage = (startMinute / 60) * 100;
    const durationHours = endHour - startHour + (endMinute - startMinute) / 60;
    const heightPercentage = durationHours * 100;

    return {
      top: `${startPercentage}%`,
      height: `${heightPercentage}%`,
    };
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 overflow-x-auto">
      <div className="grid grid-cols-[100px_repeat(5,_1fr)] min-w-[800px]">
        <div /> {/* Empty corner cell */}
        {days.map((day) => (
          <div key={day} className="p-2 border-b border-gray-200 text-center">
            <h2 className="text-lg font-semibold">{day}</h2>
          </div>
        ))}
        {hours.map((hour) => (
          <React.Fragment key={hour}>
            <div className="p-2 border-r border-gray-200">
              <span className="text-sm">{hour}</span>
            </div>
            {days.map((day) => (
              <div
                key={`${day}-${hour}`}
                className="relative h-24 border-b border-r border-gray-200"
              >
                {events
                  .filter((event) => {
                    const eventHour = parseInt(event.startTime.split(":")[0]);
                    return event.day === day && eventHour === parseInt(hour);
                  })
                  .map((event) => (
                    <div
                      key={event.id}
                      className={`absolute w-[90%] rounded p-2 overflow-hidden ${event.color} shadow-sm`}
                      style={getEventPosition(event)}
                    >
                      <p className="text-sm font-medium truncate">
                        {event.title}
                      </p>
                      <p className="text-xs truncate">
                        {event.startTime} - {event.endTime}
                      </p>
                    </div>
                  ))}
              </div>
            ))}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default WeeklyCalendar;
