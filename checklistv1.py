import streamlit as st
import json
import os
from datetime import datetime, time
import pandas as pd
from io import StringIO
import base64
from urllib.parse import quote

# Page configuration
st.set_page_config(
    page_title="Family Daily Checklist",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F5E8 0%, #F0F8F0 100%);
        border-radius: 10px;
    }
    
    .person-header {
        text-align: center;
        color: #1E6B3E;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #D4EDDA 0%, #E8F5E8 100%);
        border-radius: 10px;
        border: 2px solid #2E8B57;
    }
    
    .category-header {
        color: #1E6B3E;
        font-size: 1.3rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        background-color: #F0F8F0;
        border-left: 4px solid #2E8B57;
        border-radius: 5px;
    }
    
    .ticket-info {
        color: #666;
        font-size: 0.9rem;
        font-style: italic;
        margin-left: 1rem;
    }
    
    .stats-container {
        background: linear-gradient(135deg, #E8F5E8 0%, #D4EDDA 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #C3E6CB;
    }
    
    .download-section {
        background: #F8F9FA;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 2rem;
        border: 1px solid #DEE2E6;
    }
    
    .completion-email-section {
        background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C8 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-top: 2rem;
        border: 2px solid #4CAF50;
        text-align: center;
    }
    
    .completion-email-disabled {
        background: #F5F5F5;
        padding: 1.5rem;
        border-radius: 15px;
        margin-top: 2rem;
        border: 2px solid #CCCCCC;
        text-align: center;
        opacity: 0.6;
    }
    
    .sidebar-person-selector {
        background: #E8F5E8;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Define people
PEOPLE = ["Jonathan", "Anthony"]

# File paths (will be person-specific)
def get_checklist_file(person):
    return f"checklist_state_{person.lower()}.json"

def get_log_file(person):
    return f"checklist_log_{person.lower()}.json"

# Define the checklist items with categories
CHECKLIST_ITEMS = {
    "Morning Routine": [
        {"task": "Make Bed", "tickets": 1},
        {"task": "Eat and Clean up", "tickets": 1},
        {"task": "Dressed and sunscreen", "tickets": 2},
        {"task": "Brush hair and teeth", "tickets": 1},
    ],
    "Daily Activities": [
        {"task": "Pick up all clothes of floor", "tickets": 1},
        {"task": "Read 20 minutes", "tickets": 4},
        {"task": "Martial Arts Practice", "tickets": 0},  # Handwritten note
        {"task": "Guitar 7 minutes", "tickets": 4},
        {"task": "Math pages", "tickets": 3},
        {"task": "Workbook pages", "tickets": 3},
    ],
    "Evening Routine": [
        {"task": "Bath quickly", "tickets": 2},
        {"task": "In bed before 9", "tickets": 1},
    ],
    "Chores": [
        {"task": "Clean up toys", "tickets": 3},
        {"task": "Feed animals", "tickets": 1},
        {"task": "Fold laundry", "tickets": 2},
        {"task": "Put away laundry", "tickets": 2},
        {"task": "Vacuum", "tickets": 4},
        {"task": "Empty dishwasher", "tickets": 4},
        {"task": "Brush cats", "tickets": 2},
        {"task": "Empty trash cans", "tickets": 2},
        {"task": "Clean bathroom", "tickets": 10},
    ],
    "Behavior": [
        {"task": "Be polite no fighting", "tickets": 3},
        {"task": "Speak kind all day", "tickets": 3},
    ]
}

def get_today_key():
    """Get today's date as a string key"""
    return datetime.now().strftime("%Y-%m-%d")

def should_reset_checklist(person):
    """Check if checklist should be reset (new day)"""
    checklist_file = get_checklist_file(person)
    if not os.path.exists(checklist_file):
        return True
    
    try:
        with open(checklist_file, 'r') as f:
            data = json.load(f)
        
        last_date = data.get('date', '')
        return last_date != get_today_key()
    except:
        return True

def load_checklist_state(person):
    """Load checklist state from file"""
    if should_reset_checklist(person):
        return create_fresh_checklist()
    
    try:
        checklist_file = get_checklist_file(person)
        with open(checklist_file, 'r') as f:
            return json.load(f)
    except:
        return create_fresh_checklist()

def create_fresh_checklist():
    """Create a fresh checklist for today"""
    state = {
        'date': get_today_key(),
        'completed_tasks': {},
        'completion_times': {}
    }
    
    # Initialize all tasks as incomplete
    for category, tasks in CHECKLIST_ITEMS.items():
        for task in tasks:
            task_key = f"{category}_{task['task']}"
            state['completed_tasks'][task_key] = False
            state['completion_times'][task_key] = None
    
    return state

def save_checklist_state(person, state):
    """Save checklist state to file"""
    try:
        checklist_file = get_checklist_file(person)
        with open(checklist_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        st.error(f"Error saving checklist for {person}: {e}")

def log_completion(person, task_key, task_name, tickets, completed, timestamp):
    """Log task completion to log file"""
    try:
        log_file = get_log_file(person)
        # Load existing log
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = []
        
        # Add new entry
        log_entry = {
            'person': person,
            'date': get_today_key(),
            'timestamp': timestamp,
            'task': task_name,
            'tickets': tickets,
            'completed': completed
        }
        
        log_data.append(log_entry)
        
        # Save log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
            
    except Exception as e:
        st.error(f"Error logging completion for {person}: {e}")

def generate_log_csv(person):
    """Generate CSV content for download"""
    try:
        log_file = get_log_file(person)
        if not os.path.exists(log_file):
            return "No log data available"
        
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        if not log_data:
            return "No log data available"
        
        df = pd.DataFrame(log_data)
        return df.to_csv(index=False)
    
    except Exception as e:
        return f"Error generating log: {e}"

def create_email_body(person):
    """Create email body for completion notification"""
    state_key = f'checklist_state_{person}'
    state = st.session_state[state_key]
    
    total_tasks = sum(len(tasks) for tasks in CHECKLIST_ITEMS.values())
    total_tickets = sum(task['tickets'] for tasks in CHECKLIST_ITEMS.values() for task in tasks)
    
    email_body = f"""Hi!

{person} has completed their daily checklist for {datetime.now().strftime('%A, %B %d, %Y')}!

🎉 CHECKLIST COMPLETE! 🎉

📊 Final Stats:
• All {total_tasks} tasks completed ✅
• All {total_tickets} tickets earned 🎫
• 100% completion rate 🏆

✅ Completed Tasks:
"""
    
    for category, tasks in CHECKLIST_ITEMS.items():
        email_body += f"\n{category}:\n"
        for task in tasks:
            tickets_text = f" ({task['tickets']} tickets)" if task['tickets'] > 0 else ""
            email_body += f"  ✓ {task['task']}{tickets_text}\n"
    
    email_body += f"""
Great job {person}! 🌟

The detailed log file is attached for your records.

Best regards,
{person}'s Daily Checklist App
"""
    
    return email_body

def create_mailto_link(person, subject, body):
    """Create a mailto link that opens the default email client"""
    # URL encode the subject and body
    encoded_subject = quote(subject)
    encoded_body = quote(body)
    
    mailto_link = f"mailto:?subject={encoded_subject}&body={encoded_body}"
    return mailto_link

def is_checklist_complete(person):
    """Check if all tasks are completed for a person"""
    state_key = f'checklist_state_{person}'
    if state_key not in st.session_state:
        return False
    
    state = st.session_state[state_key]
    
    for category, tasks in CHECKLIST_ITEMS.items():
        for task in tasks:
            task_key = f"{category}_{task['task']}"
            if not state['completed_tasks'].get(task_key, False):
                return False
    
    return True

def generate_combined_log_csv():
    """Generate combined CSV for all people"""
    try:
        all_data = []
        for person in PEOPLE:
            log_file = get_log_file(person)
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    person_data = json.load(f)
                    all_data.extend(person_data)
        
        if not all_data:
            return "No log data available"
        
        df = pd.DataFrame(all_data)
        return df.to_csv(index=False)
    
    except Exception as e:
        return f"Error generating combined log: {e}"

def render_checklist_for_person(person):
    """Render the checklist interface for a specific person"""
    
    # Person header
    st.markdown(f'<div class="person-header">📋 {person}\'s Checklist</div>', unsafe_allow_html=True)
    
    # Get or initialize session state for this person
    state_key = f'checklist_state_{person}'
    if state_key not in st.session_state:
        st.session_state[state_key] = load_checklist_state(person)
    
    # Display current date
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    st.markdown(f"<h4 style='text-align: center; color: #666;'>{current_date}</h4>", unsafe_allow_html=True)
    
    # Calculate statistics
    total_tasks = sum(len(tasks) for tasks in CHECKLIST_ITEMS.values())
    total_tickets = sum(task['tickets'] for tasks in CHECKLIST_ITEMS.values() for task in tasks)
    completed_tasks = sum(1 for completed in st.session_state[state_key]['completed_tasks'].values() if completed)
    earned_tickets = sum(
        task['tickets'] for category, tasks in CHECKLIST_ITEMS.items() 
        for task in tasks if st.session_state[state_key]['completed_tasks'].get(f"{category}_{task['task']}", False)
    )
    
    # Stats display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Completed Tasks", f"{completed_tasks}/{total_tasks}")
    with col2:
        st.metric("Tickets Earned", f"{earned_tickets}/{total_tickets}")
    with col3:
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    with col4:
        ticket_rate = (earned_tickets / total_tickets * 100) if total_tickets > 0 else 0
        st.metric("Ticket Rate", f"{ticket_rate:.1f}%")
    
    # Progress bar
    st.progress(completion_rate / 100)
    
    # Checklist sections
    for category, tasks in CHECKLIST_ITEMS.items():
        st.markdown(f'<div class="category-header">{category}</div>', unsafe_allow_html=True)
        
        for task in tasks:
            task_key = f"{category}_{task['task']}"
            
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                # Create checkbox with unique key for this person
                checkbox_key = f"checkbox_{person}_{task_key}"
                current_state = st.session_state[state_key]['completed_tasks'].get(task_key, False)
                new_state = st.checkbox(
                    task['task'],
                    value=current_state,
                    key=checkbox_key
                )
                
                # Handle state change
                if new_state != current_state:
                    st.session_state[state_key]['completed_tasks'][task_key] = new_state
                    timestamp = datetime.now().isoformat()
                    st.session_state[state_key]['completion_times'][task_key] = timestamp if new_state else None
                    
                    # Log the change
                    log_completion(person, task_key, task['task'], task['tickets'], new_state, timestamp)
                    
                    # Save state
                    save_checklist_state(person, st.session_state[state_key])
                    
                    # Rerun to update display
                    st.rerun()
            
            with col2:
                if task['tickets'] > 0:
                    ticket_text = "🎫" * task['tickets']
                    st.markdown(f'<div class="ticket-info">{ticket_text} ({task["tickets"]} tickets)</div>', 
                              unsafe_allow_html=True)
    
    # Completion Email Section - Only show if all tasks are complete
    is_complete = is_checklist_complete(person)
    
    if is_complete:
        st.markdown('<div class="completion-email-section">', unsafe_allow_html=True)
        st.markdown("### 🎉 CHECKLIST COMPLETE! 🎉")
        st.markdown(f"**{person}** has finished all tasks!")
        
        # Create email content
        email_subject = f"{person}'s Daily Checklist Complete - {get_today_key()}"
        email_body = create_email_body(person)
        
        # Create download for CSV to attach manually
        csv_content = generate_log_csv(person)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Mailto link button
            mailto_link = create_mailto_link(person, email_subject, email_body)
            st.markdown(f"""
            <a href="{mailto_link}" target="_blank">
                <button style="
                    background: linear-gradient(45deg, #4CAF50, #45a049);
                    color: white;
                    padding: 15px 30px;
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    width: 100%;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                ">
                    📧 Send Completion Email
                </button>
            </a>
            """, unsafe_allow_html=True)
            st.markdown("*Opens your default email app*")
        
        with col2:
            # Download CSV for manual attachment
            if csv_content != "No log data available" and not csv_content.startswith("Error"):
                st.download_button(
                    label="📎 Download Log for Attachment",
                    data=csv_content,
                    file_name=f"{person.lower()}_checklist_complete_{get_today_key()}.csv",
                    mime="text/csv",
                    key=f"completion_download_{person}"
                )
                st.markdown("*Download this to attach to your email*")
            
        st.markdown("**Instructions:**")
        st.markdown("1. Click '📧 Send Completion Email' to open your email app")
        st.markdown("2. Add the recipient's email address")
        st.markdown("3. Download and attach the log file if needed")
        st.markdown("4. Send the email!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Show grayed out section when incomplete
        incomplete_count = sum(len(tasks) for tasks in CHECKLIST_ITEMS.values()) - sum(1 for completed in st.session_state[f'checklist_state_{person}']['completed_tasks'].values() if completed)
        
        st.markdown('<div class="completion-email-disabled">', unsafe_allow_html=True)
        st.markdown("### 📧 Completion Email")
        st.markdown(f"**{incomplete_count} tasks remaining** before email becomes available")
        
        st.markdown("""
        <button style="
            background: #CCCCCC;
            color: #666666;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: not-allowed;
            width: 100%;
            opacity: 0.6;
        " disabled>
            📧 Send Completion Email (Complete All Tasks First)
        </button>
        """, unsafe_allow_html=True)
        
        st.markdown("*Complete all tasks to unlock the completion email*")
        st.markdown('</div>', unsafe_allow_html=True)

    # Download section for this person
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.markdown(f"### 📥 Download {person}'s Log")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button(f"📊 Generate {person}'s Log", key=f"download_{person}"):
            csv_content = generate_log_csv(person)
            if csv_content != "No log data available" and not csv_content.startswith("Error"):
                st.download_button(
                    label=f"Download {person}'s CSV Log",
                    data=csv_content,
                    file_name=f"checklist_log_{person.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=f"download_btn_{person}"
                )
            else:
                st.warning(csv_content)
    
    with col2:
        if st.button(f"🔄 Reset {person}'s Checklist", key=f"reset_{person}"):
            st.session_state[state_key] = create_fresh_checklist()
            save_checklist_state(person, st.session_state[state_key])
            st.success(f"{person}'s checklist reset successfully!")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown('<div class="main-header">👨‍👦‍👦 Family Daily Checklist</div>', unsafe_allow_html=True)
    
    # Sidebar for person selection
    with st.sidebar:
        st.markdown('<div class="sidebar-person-selector">', unsafe_allow_html=True)
        st.markdown("### 👥 Select Person")
        selected_person = st.selectbox(
            "Choose a family member:",
            PEOPLE,
            key="person_selector"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Family overview
        st.markdown("### 📊 Family Overview")
        
        family_stats = {}
        for person in PEOPLE:
            state_key = f'checklist_state_{person}'
            if state_key not in st.session_state:
                st.session_state[state_key] = load_checklist_state(person)
            
            total_tasks = sum(len(tasks) for tasks in CHECKLIST_ITEMS.values())
            completed_tasks = sum(1 for completed in st.session_state[state_key]['completed_tasks'].values() if completed)
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Add completion status emoji
            status_emoji = "🎉" if is_checklist_complete(person) else "📝"
            
            family_stats[person] = {
                'completed': completed_tasks,
                'total': total_tasks,
                'rate': completion_rate,
                'emoji': status_emoji
            }
        
        for person, stats in family_stats.items():
            st.metric(
                f"{stats['emoji']} {person}",
                f"{stats['completed']}/{stats['total']}",
                f"{stats['rate']:.1f}%"
            )
        
        # Combined download
        st.markdown("### 📥 Combined Reports")
        if st.button("📊 Generate Combined Log"):
            csv_content = generate_combined_log_csv()
            if csv_content != "No log data available" and not csv_content.startswith("Error"):
                st.download_button(
                    label="Download Combined Family Log",
                    data=csv_content,
                    file_name=f"family_checklist_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning(csv_content)
        
        # Auto-refresh check
        st.markdown("### 🔄 Daily Reset")
        if st.button("🔄 Check for New Day"):
            reset_count = 0
            for person in PEOPLE:
                if should_reset_checklist(person):
                    state_key = f'checklist_state_{person}'
                    st.session_state[state_key] = create_fresh_checklist()
                    save_checklist_state(person, st.session_state[state_key])
                    reset_count += 1
            
            if reset_count > 0:
                st.success(f"New day detected! Reset {reset_count} checklist(s).")
                st.rerun()
            else:
                st.info("Still the same day - no reset needed.")
    
    # Main content area - show selected person's checklist
    render_checklist_for_person(selected_person)

if __name__ == "__main__":
    main()
