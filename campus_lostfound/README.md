# Campus Lost & Found Management System

A modern, full-stack web application for managing lost and found items on campus. Built with Flask, MySQL, and a beautiful glassmorphism UI design.

## Features

- **Modern Glassmorphism Design**: Beautiful dark gradient aesthetic with smooth animations
- **Smart Matching Algorithm**: Automatic item matching using keyword similarity, category matching, and image similarity
- **Multi-step Forms**: Intuitive forms for reporting lost and found items
- **Image Upload**: Drag-and-drop image support with preview
- **User Authentication**: Secure login/signup system with role-based access
- **Admin Dashboard**: Comprehensive admin panel with analytics and claim management
- **Responsive Design**: Mobile-friendly interface that works on all devices
- **Real-time Notifications**: Flash messages and notification system
- **Search & Filter**: Advanced filtering by category, location, and status

## Tech Stack

- **Backend**: Python 3.8+, Flask, SQLAlchemy, MySQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: MySQL 8.0+
- **Image Processing**: Pillow, imagehash
- **UI/UX**: Glassmorphism design with custom CSS animations

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip and virtualenv

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd campus_lostfound
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   
   Create a MySQL database:
   ```sql
   CREATE DATABASE campus_lostfound;
   ```
   
   Update the database URL in `config.py`:
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/campus_lostfound'
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```
   This will automatically create the tables and a default admin user.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   
   Open your browser and navigate to `http://localhost:5000`
   
   **Default Admin Login:**
   - Email: admin@campus.edu
   - Password: admin123

## Database Schema

The application uses the following tables:

- **users**: User accounts with role-based permissions
- **items**: Lost and found items with metadata
- **claims**: User claims for items
- **matches**: Automatic matching results between lost and found items

## Smart Matching Algorithm

The system uses a sophisticated matching algorithm that considers:

1. **Keyword Similarity**: Jaccard similarity between item keywords
2. **Category Matching**: Bonus points for same category items
3. **Image Similarity**: Perceptual hash comparison using imagehash

Match scores > 0.3 are considered valid matches and displayed on item detail pages.

## Project Structure

```
campus_lostfound/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── db.py                  # Database models and initialization
├── matching.py            # Smart matching algorithm
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css      # Custom CSS with glassmorphism
│   ├── js/
│   │   └── main.js        # JavaScript interactions
│   └── uploads/           # User uploaded images
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Home page
    ├── login.html         # Login page
    ├── signup.html        # Registration page
    ├── browse.html        # Browse items page
    ├── item_detail.html   # Item detail page
    ├── post_lost.html     # Report lost item form
    ├── post_found.html    # Report found item form
    ├── dashboard.html     # User dashboard
    └── admin_dashboard.html # Admin dashboard
```

## Features in Detail

### Home Page
- Animated particle background
- Live statistics display
- Recent items carousel
- Clear CTAs for reporting lost/found items

### Authentication
- Secure password hashing
- Session management
- Role-based access control
- Glassmorphism login/signup forms

### Item Management
- Multi-step forms with progress indicators
- Drag-and-drop image upload
- Keyword tagging system
- Category and location tracking

### Smart Matching
- Automatic matching when new items are posted
- Match score display as percentages
- Top 3 matches shown on item detail pages

### Admin Dashboard
- Analytics with Chart.js visualizations
- Pending claims management
- User and item management
- System statistics

### User Dashboard
- Personal item management
- Claim tracking
- Edit/delete functionality

## Security Features

- Password hashing with Werkzeug
- SQL injection prevention with parameterized queries
- File upload restrictions (images only)
- Session-based authentication
- Admin role protection

## Customization

### Colors and Theme
The application uses CSS variables for easy customization:

```css
:root {
  --bg-primary: #0d0d1a;
  --accent-primary: #7c3aed;
  --lost-color: #ef4444;
  --found-color: #10b981;
  /* ... more variables */
}
```

### Adding New Categories
Update the category options in the post forms and database schema as needed.

### Matching Algorithm
Adjust matching thresholds in `config.py`:

```python
MATCH_THRESHOLD = 0.3
CATEGORY_BONUS = 0.3
IMAGE_BONUS = 0.2
```

## Deployment

### Production Considerations

1. **Security**
   - Change the default `SECRET_KEY`
   - Use environment variables for sensitive data
   - Enable HTTPS

2. **Database**
   - Use a production MySQL instance
   - Set up proper backups

3. **File Storage**
   - Configure proper file upload limits
   - Consider cloud storage for images

4. **Performance**
   - Enable database connection pooling
   - Consider Redis for session storage
   - Set up proper caching

### Example Production Config

```python
import os

class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team

---

**Built with ❤️ for campus communities**
