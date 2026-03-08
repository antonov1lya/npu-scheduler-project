import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from collections import defaultdict, deque
import sys
import subprocess

class TaskSchedulerScorer:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.n = 0
        self.n_vector = 0
        self.n_cube = 0
        self.tasks = {}
        self.dependencies = defaultdict(list)
        self.reverse_dependencies = defaultdict(list)
        self.core_schedules = []
        self.core_assignments = {}
        self.start_times = {}
        self.finish_times = {}
        self.core_available_times = []
        self.valid = True
        self.error_message = ""
        
    def read_input(self):
        with open(self.input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines:
            self.valid = False
            self.error_message = "Empty input file"
            return
            
        try:
            # Parse first line
            first_line = lines[0].split()
            self.n = int(first_line[0])
            self.n_vector = int(first_line[1])
            self.n_cube = int(first_line[2])
            
            # Parse tasks
            for i in range(1, self.n + 1):
                if i >= len(lines):
                    self.valid = False
                    self.error_message = f"Not enough lines for tasks, expected {self.n} tasks"
                    return
                    
                task_line = lines[i].split()
                if len(task_line) < 2:
                    self.valid = False
                    self.error_message = f"Invalid task line: {lines[i]}"
                    return
                    
                task_type = task_line[0]
                duration = int(task_line[1])
                self.tasks[i] = {
                    'type': task_type,
                    'duration': duration,
                    'id': i
                }
            
            # Parse dependencies
            m_line = self.n + 1
            if m_line >= len(lines):
                self.valid = False
                self.error_message = "Missing dependencies line"
                return
                
            m = int(lines[m_line])
            
            for i in range(m_line + 1, m_line + 1 + m):
                if i >= len(lines):
                    self.valid = False
                    self.error_message = f"Not enough lines for dependencies, expected {m} dependencies"
                    return
                    
                dep_line = lines[i].split()
                if len(dep_line) < 2:
                    self.valid = False
                    self.error_message = f"Invalid dependency line: {lines[i]}"
                    return
                    
                x, y = map(int, dep_line)
                self.dependencies[x].append(y)
                self.reverse_dependencies[y].append(x)
        except Exception as e:
            self.valid = False
            self.error_message = f"Error parsing input: {str(e)}"
    def run_subprocess(self):
        # Run a subprocess command and capture output
        try:
           result = subprocess.run(
                ['./npu_scheduler', 'input.txt', './', 'base', '30'],
                cwd='npu_scheduler/build',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.valid = False
            self.error_message = f"Execution subprocess error: {e.stderr.strip()}"

    def read_output(self):
        with open(self.output_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines:
            self.valid = False
            self.error_message = "Empty output file"
            return
            
        if len(lines) != self.n_vector + self.n_cube:
            self.valid = False
            self.error_message = f"Expected {self.n_vector + self.n_cube} lines for cores, got {len(lines)}"
            return
        
        self.core_schedules = []
        task_count = {}
        
        try:
            # Parse vector cores
            for i in range(self.n_vector):
                if i >= len(lines):
                    self.valid = False
                    self.error_message = f"Not enough lines for vector cores"
                    return
                    
                line_parts = lines[i].split()
                if not line_parts:
                    self.valid = False
                    self.error_message = f"Empty line for vector core {i+1}"
                    return
                
                k = int(line_parts[0])
                if len(line_parts) < 1 + k:
                    self.valid = False
                    self.error_message = f"Not enough tasks specified for vector core {i+1}"
                    return
                    
                tasks = list(map(int, line_parts[1:1+k]))
                
                # Check task types for vector core
                for task_id in tasks:
                    if task_id not in self.tasks:
                        self.valid = False
                        self.error_message = f"Task {task_id} not found in input"
                        return
                        
                    if self.tasks[task_id]['type'] != 'V':
                        self.valid = False
                        self.error_message = f"Task {task_id} of type {self.tasks[task_id]['type']} assigned to vector core"
                        return
                    self.core_assignments[task_id] = i
                    
                    # Count task occurrences
                    task_count[task_id] = task_count.get(task_id, 0) + 1
                
                self.core_schedules.append(tasks)
            
            # Parse cube cores
            for i in range(self.n_vector, self.n_vector + self.n_cube):
                if i >= len(lines):
                    self.valid = False
                    self.error_message = f"Not enough lines for cube cores"
                    return
                    
                line_parts = lines[i].split()
                if not line_parts:
                    self.valid = False
                    self.error_message = f"Empty line for cube core {i+1 - self.n_vector}"
                    return
                
                k = int(line_parts[0])
                if len(line_parts) < 1 + k:
                    self.valid = False
                    self.error_message = f"Not enough tasks specified for cube core {i+1 - self.n_vector}"
                    return
                    
                tasks = list(map(int, line_parts[1:1+k]))
                
                # Check task types for cube core
                for task_id in tasks:
                    if task_id not in self.tasks:
                        self.valid = False
                        self.error_message = f"Task {task_id} not found in input"
                        return
                        
                    if self.tasks[task_id]['type'] != 'C':
                        self.valid = False
                        self.error_message = f"Task {task_id} of type {self.tasks[task_id]['type']} assigned to cube core"
                        return
                    self.core_assignments[task_id] = i
                    
                    # Count task occurrences
                    task_count[task_id] = task_count.get(task_id, 0) + 1
                
                self.core_schedules.append(tasks)
            
            # Check if all tasks are scheduled exactly once
            for task_id in range(1, self.n + 1):
                if task_count.get(task_id, 0) != 1:
                    self.valid = False
                    self.error_message = f"Task {task_id} appears {task_count.get(task_id, 0)} times (should be exactly once)"
                    return
        except Exception as e:
            self.valid = False
            self.error_message = f"Error parsing output: {str(e)}"
    
    def simulate_execution(self):
        if not self.valid:
            return float('inf')
        
        # Initialize
        self.start_times = {}
        self.finish_times = {}
        self.core_available_times = [0] * (self.n_vector + self.n_cube)
        
        # Create a copy of dependencies to track remaining dependencies
        remaining_dependencies = {}
        for task_id in range(1, self.n + 1):
            remaining_dependencies[task_id] = set(self.reverse_dependencies[task_id])
        
        # Create task queues for each core (to track which tasks are ready to be scheduled in order)
        core_task_queues = []
        for core_schedule in self.core_schedules:
            core_task_queues.append(deque(core_schedule))
        
        # Track which tasks are completed
        completed_tasks = set()
        
        # Main simulation loop - we advance time until all tasks are completed
        current_time = 0
        max_time = 0
        
        while len(completed_tasks) < self.n:
            # Find the next event time (when a core becomes available or a dependency is satisfied)
            next_time = float('inf')
            progress = False
            
            # Try to schedule tasks on each core
            for core_id in range(len(self.core_schedules)):
                if not core_task_queues[core_id]:
                    continue  # No more tasks on this core
                
                task_id = core_task_queues[core_id][0]
                
                # Check if task is ready (all dependencies satisfied)
                if remaining_dependencies[task_id]:
                    # Task is not ready, check when its last dependency will finish
                    last_dep_finish = 0
                    for dep in remaining_dependencies[task_id]:
                        if dep in self.finish_times:
                            last_dep_finish = max(last_dep_finish, self.finish_times[dep])
                        else:
                            # Dependency not yet scheduled, can't schedule this task yet
                            last_dep_finish = float('inf')
                            break
                    
                    if last_dep_finish == float('inf'):
                        continue  # Can't schedule this task yet
                else:
                    last_dep_finish = 0
                
                # Task is ready, check core availability
                earliest_start = max(self.core_available_times[core_id], last_dep_finish)
                
                if earliest_start < next_time:
                    next_time = earliest_start
                    progress = True
            
            if not progress:
                # Check if we have any chance to make progress
                if next_time == float('inf'):
                    self.valid = False
                    self.error_message = "Deadlock detected - no progress possible"
                    return float('inf')
            
            # Advance to next_time and schedule ready tasks
            current_time = next_time
            
            for core_id in range(len(self.core_schedules)):
                if not core_task_queues[core_id]:
                    continue
                
                task_id = core_task_queues[core_id][0]
                
                # Check if task is ready and core is available
                if (not remaining_dependencies[task_id] and 
                    self.core_available_times[core_id] <= current_time):
                    
                    # Calculate actual start time (considering dependencies)
                    dep_finish_time = 0
                    for dep in self.reverse_dependencies[task_id]:
                        dep_finish_time = max(dep_finish_time, self.finish_times[dep])
                    
                    actual_start = max(current_time, dep_finish_time)
                    
                    # Schedule the task
                    self.start_times[task_id] = actual_start
                    finish_time = actual_start + self.tasks[task_id]['duration']
                    self.finish_times[task_id] = finish_time
                    self.core_available_times[core_id] = finish_time
                    
                    # Remove task from queue and mark as completed
                    core_task_queues[core_id].popleft()
                    completed_tasks.add(task_id)
                    
                    # Update dependencies for dependent tasks
                    for dependent in self.dependencies[task_id]:
                        remaining_dependencies[dependent].discard(task_id)
                    
                    progress = True
            
            if not progress and len(completed_tasks) < self.n:
                # No progress in this iteration, but we still have tasks
                # This might happen if all ready tasks are blocked by core availability
                # Find the minimum time when any core becomes available
                min_core_available = min(self.core_available_times)
                if min_core_available > current_time:
                    current_time = min_core_available
                else:
                    # This shouldn't happen, but if it does, we have a deadlock
                    self.valid = False
                    self.error_message = "Deadlock detected - no progress after advancing time"
                    return float('inf')
        
        # Calculate total execution time
        if self.finish_times:
            total_time = max(self.finish_times.values())
        else:
            total_time = 0
            
        return total_time
    
    def calculate_score(self):
        self.read_input()
        if not self.valid:
            return 0, self.error_message, None
        
        # self.run_subprocess()
        # if not self.valid:
        #     return 0, self.error_message, None

        self.read_output()
        if not self.valid:
            return 0, self.error_message, None
        
        total_duration = sum(task['duration'] for task in self.tasks.values())
        total_time = self.simulate_execution()
        
        if not self.valid:
            return 0, self.error_message, None
        
        if total_time == 0:
            relative_score = 0
        else:
            relative_score = 10**6 * total_duration / total_time
        
        return relative_score, f"Success - Total time: {total_time}, Score: {relative_score:.2f}", total_time
    
    def calculate_core_utilization(self):
        """Calculate actual core utilization based on task execution times"""
        if not self.valid or not self.start_times:
            return {}
        
        max_time = max(self.finish_times.values()) if self.finish_times else 0
        
        core_busy_time = [0] * (self.n_vector + self.n_cube)
        
        # Calculate busy time for each core
        for core_id in range(len(self.core_schedules)):
            core_schedule = self.core_schedules[core_id]
            for task_id in core_schedule:
                if task_id in self.start_times:
                    duration = self.finish_times[task_id] - self.start_times[task_id]
                    core_busy_time[core_id] += duration
        
        # Calculate utilization percentage
        utilizations = {}
        for core_id in range(len(self.core_schedules)):
            core_type = "Vector" if core_id < self.n_vector else "Cube"
            core_num = core_id if core_id < self.n_vector else core_id - self.n_vector
            utilization = (core_busy_time[core_id] / max_time * 100) if max_time > 0 else 0
            utilizations[f"{core_type} Core {core_num}"] = utilization
        
        return utilizations
    
    def find_inefficiencies(self):
        """Find periods of inefficiency in the schedule"""
        if not self.valid or not self.start_times:
            return [], []
        
        max_time = max(self.finish_times.values())
        idle_periods = []
        dependency_delays = []
        
        # Find idle periods on each core
        for core_id in range(len(self.core_schedules)):
            core_schedule = self.core_schedules[core_id]
            core_type = "Vector" if core_id < self.n_vector else "Cube"
            core_num = core_id if core_id < self.n_vector else core_id - self.n_vector
            
            # Sort tasks by start time for this core
            tasks_on_core = []
            for task_id in core_schedule:
                if task_id in self.start_times:
                    tasks_on_core.append((self.start_times[task_id], self.finish_times[task_id], task_id))
            
            tasks_on_core.sort()
            
            # Find idle periods
            current_time = 0
            for start, finish, task_id in tasks_on_core:
                if start > current_time:
                    # Idle period found
                    idle_periods.append({
                        'core_id': core_id,
                        'core_type': core_type,
                        'core_num': core_num,
                        'start': current_time,
                        'end': start,
                        'duration': start - current_time,
                        'task_id': None
                    })
                current_time = finish
            
            # Check for idle time at the end
            if current_time < max_time:
                idle_periods.append({
                    'core_id': core_id,
                    'core_type': core_type,
                    'core_num': core_num,
                    'start': current_time,
                    'end': max_time,
                    'duration': max_time - current_time,
                    'task_id': None
                })
        
        # Find dependency delays
        for task_id in range(1, self.n + 1):
            if task_id not in self.start_times:
                continue
                
            # Find when all dependencies are finished
            last_dependency_finish = 0
            for dep in self.reverse_dependencies[task_id]:
                if dep in self.finish_times:
                    last_dependency_finish = max(last_dependency_finish, self.finish_times[dep])
            
            # Check if task started later than it could have due to core availability
            core_id = self.core_assignments[task_id]
            core_schedule = self.core_schedules[core_id]
            task_index = core_schedule.index(task_id)
            
            # Find when the core becomes available for this task
            core_available_time = 0
            if task_index > 0:
                prev_task = core_schedule[task_index - 1]
                if prev_task in self.finish_times:
                    core_available_time = self.finish_times[prev_task]
            
            # The earliest possible start time is the maximum of when dependencies finish and core becomes available
            earliest_start = max(last_dependency_finish, core_available_time)
            
            # If the task started later than earliest possible, there's a delay
            if self.start_times[task_id] > earliest_start:
                dependency_delays.append({
                    'task_id': task_id,
                    'earliest_start': earliest_start,
                    'actual_start': self.start_times[task_id],
                    'delay': self.start_times[task_id] - earliest_start,
                    'reason': 'Core busy' if earliest_start == core_available_time else 'Dependencies'
                })
        
        return idle_periods, dependency_delays
    
    def visualize_schedule(self, save_png = True, output_image="schedule.png"):
        if not self.valid or not self.start_times:
            print("Cannot visualize - invalid schedule")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Color mapping for tasks
        colors = {'V': 'blue', 'C': 'red'}
        
        # Plot 1: Gantt chart by core
        max_time = max(self.finish_times.values())
        
        # Vector cores
        for core_idx in range(self.n_vector):
            core_schedule = self.core_schedules[core_idx]
            y_pos = core_idx
            
            for task_id in core_schedule:
                start = self.start_times[task_id]
                duration = self.tasks[task_id]['duration']
                task_type = self.tasks[task_id]['type']
                
                rect = patches.Rectangle((start, y_pos - 0.4), duration, 0.8, 
                                       facecolor=colors[task_type], alpha=0.7,
                                       edgecolor='black', linewidth=1)
                ax1.add_patch(rect)
                
                # Add task ID text
                # ax1.text(start + duration/2, y_pos, f'T{task_id}', 
                #         ha='center', va='center', fontsize=8, color='white')
        
        # Cube cores  
        for core_idx in range(self.n_cube):
            core_schedule = self.core_schedules[self.n_vector + core_idx]
            y_pos = self.n_vector + core_idx
            
            for task_id in core_schedule:
                start = self.start_times[task_id]
                duration = self.tasks[task_id]['duration']
                task_type = self.tasks[task_id]['type']
                
                rect = patches.Rectangle((start, y_pos - 0.4), duration, 0.8, 
                                       facecolor=colors[task_type], alpha=0.7,
                                       edgecolor='black', linewidth=1)
                ax1.add_patch(rect)
                
                # Add task ID text
                # ax1.text(start + duration/2, y_pos, f'T{task_id}', 
                #         ha='center', va='center', fontsize=8, color='white')
        
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Core')
        ax1.set_title('Task Schedule by Core')
        ax1.set_xlim(0, max_time * 1.1)
        ax1.set_ylim(-0.5, self.n_vector + self.n_cube - 0.5)
        ax1.grid(True, alpha=0.3)
        
        # Create legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', alpha=0.7, label='Vector Tasks'),
            Patch(facecolor='red', alpha=0.7, label='Cube Tasks')
        ]
        ax1.legend(handles=legend_elements, loc='upper right')
        
        # Plot 2: Idle periods
        idle_periods, _ = self.find_inefficiencies()
        
        for idle in idle_periods:
            core_id = idle['core_id']
            y_pos = core_id
            rect = patches.Rectangle((idle['start'], y_pos - 0.4), idle['duration'], 0.8, 
                                   facecolor='yellow', alpha=0.5,
                                   edgecolor='orange', linewidth=1)
            ax2.add_patch(rect)
            
            # Add idle time text for significant idle periods
            # if idle['duration'] > max_time * 0.05:  # Only show text for idle periods > 5% of total time
            #     ax2.text(idle['start'] + idle['duration']/2, y_pos, f'Idle: {idle["duration"]}', 
            #             ha='center', va='center', fontsize=7, color='black')
        
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Core')
        ax2.set_title('Idle Periods (Yellow = Idle Time)')
        ax2.set_xlim(0, max_time * 1.1)
        ax2.set_ylim(-0.5, self.n_vector + self.n_cube - 0.5)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_png:
            plt.savefig(output_image, dpi=300, bbox_inches='tight')
        # plt.show()
        
        # Print detailed analysis
        self.print_detailed_analysis()
        return fig 
    
    def print_detailed_analysis(self):
        """Print detailed analysis of the schedule"""
        if not self.valid or not self.start_times:
            print("Cannot analyze - invalid schedule")
            return
        
        max_time = max(self.finish_times.values())
        total_duration = sum(task['duration'] for task in self.tasks.values())
        
        print("\n=== DETAILED SCHEDULE ANALYSIS ===")
        print(f"Total execution time: {max_time}")
        print(f"Total task duration: {total_duration}")
        
        # Calculate efficiency metrics
        total_core_time = max_time * (self.n_vector + self.n_cube)
        efficiency = total_duration / total_core_time * 100 if total_core_time > 0 else 0
        print(f"Overall efficiency: {efficiency:.1f}%")
        
        # Core utilization
        utilizations = self.calculate_core_utilization()
        print("\n=== CORE UTILIZATION ===")
        for core, util in utilizations.items():
            print(f"{core}: {util:.1f}%")
        
        # Inefficiencies
        idle_periods, dependency_delays = self.find_inefficiencies()
        
        print(f"\n=== INEFFICIENCIES ===")
        
        # Idle time analysis
        total_idle_time = sum(idle['duration'] for idle in idle_periods)
        print(f"Total idle time: {total_idle_time}")
        print(f"Idle time percentage: {total_idle_time / total_core_time * 100:.1f}%")
        
        if idle_periods:
            print("\nTop 5 longest idle periods:")
            sorted_idle = sorted(idle_periods, key=lambda x: x['duration'], reverse=True)
            for idle in sorted_idle[:5]:
                print(f"  {idle['core_type']} Core {idle['core_num']}: {idle['duration']} time units " +
                      f"(from {idle['start']} to {idle['end']})")
        
        # Dependency delay analysis
        total_delay = sum(delay['delay'] for delay in dependency_delays)
        print(f"\nTotal dependency/core delay: {total_delay}")
        
        if dependency_delays:
            print("\nTop 5 longest delays:")
            sorted_delays = sorted(dependency_delays, key=lambda x: x['delay'], reverse=True)
            for delay in sorted_delays[:5]:
                print(f"  Task {delay['task_id']}: {delay['delay']} time units " +
                      f"(could start at {delay['earliest_start']}, actually started at {delay['actual_start']})")
        
        # Critical path analysis
        print(f"\n=== CRITICAL PATH ANALYSIS ===")
        critical_path_length = self.calculate_critical_path_length()
        print(f"Critical path length: {critical_path_length}")
        print(f"Schedule makespan / Critical path: {max_time / critical_path_length:.2f}")
        
        # Suggestions for improvement
        print(f"\n=== SUGGESTIONS ===")
        if total_idle_time > total_duration * 0.2:  # If more than 20% idle time
            print("• High idle time: Consider better load balancing between cores")
        
        if len(dependency_delays) > self.n * 0.3:  # If more than 30% of tasks have delays
            print("• Many dependency delays: Consider reordering tasks to minimize waiting")
        
        if max_time > critical_path_length * 1.5:  # If makespan is much longer than critical path
            print("• Schedule is much longer than critical path: Focus on optimizing critical path tasks")
    
    def calculate_critical_path_length(self):
        """Calculate the length of the critical path in the task graph"""
        if not self.tasks:
            return 0
        
        # Calculate earliest start times using topological order
        earliest_start = {task_id: 0 for task_id in self.tasks}
        max_finish = 0
        
        # We need to process tasks in topological order
        # For simplicity, we'll use multiple passes
        changed = True
        while changed:
            changed = False
            for task_id in self.tasks:
                # Calculate earliest start based on dependencies
                dep_finish = 0
                for dep in self.reverse_dependencies[task_id]:
                    dep_finish = max(dep_finish, earliest_start[dep] + self.tasks[dep]['duration'])
                
                if dep_finish > earliest_start[task_id]:
                    earliest_start[task_id] = dep_finish
                    changed = True
                
                # Update max finish time
                finish_time = earliest_start[task_id] + self.tasks[task_id]['duration']
                if finish_time > max_finish:
                    max_finish = finish_time
        
        return max_finish

def main():
    if len(sys.argv) < 3:
        print("Usage: python scorer.py <input_file> <output_file> [visualization_output]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    visualization_output = sys.argv[3] if len(sys.argv) > 3 else "schedule.png"
    
    scorer = TaskSchedulerScorer(input_file, output_file)
    score, message, total_time = scorer.calculate_score()
    
    print(f"Score: {score:.2f}")
    print(f"Message: {message}")
    
    if scorer.valid:
        scorer.visualize_schedule(save_png=True, output_image=visualization_output)

if __name__ == "__main__":
    main()