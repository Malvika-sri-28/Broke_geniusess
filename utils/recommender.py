import re
from database import Service

def clean_text(text):
    """Convert text to lower case, strip punctuation, filter stop words, and return set of words."""
    if not text:
        return set()
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    words = cleaned.split()
    
    # Common English stop words
    stop_words = {
        'and', 'the', 'for', 'with', 'you', 'your', 'this', 'that', 'from', 
        'our', 'are', 'i', 'a', 'to', 'in', 'of', 'on', 'is', 'it', 'or', 
        'at', 'an', 'about', 'by', 'my', 'me', 'we', 'he', 'she', 'they', 
        'can', 'will', 'would', 'should', 'was', 'were', 'been', 'has', 'have'
    }
    
    return {w for w in words if len(w) > 2 and w not in stop_words}

def get_recommended_services(service, limit=3):
    """
    Computes text similarity between the active service and all other listings.
    Returns the top 'limit' listings with non-zero similarity.
    """
    # Build term vocabulary for the current service
    current_terms = clean_text(service.title) | clean_text(service.description)
    if service.keywords:
        current_terms.update({k.strip().lower() for k in service.keywords.split(',') if len(k.strip()) > 2})
        
    # Get all other services
    all_other_services = Service.query.filter(Service.id != service.id).all()
    scored_services = []
    
    for other in all_other_services:
        other_terms = clean_text(other.title) | clean_text(other.description)
        if other.keywords:
            other_terms.update({k.strip().lower() for k in other.keywords.split(',') if len(k.strip()) > 2})
            
        intersection = current_terms.intersection(other_terms)
        union = current_terms.union(other_terms)
        
        # Calculate Jaccard similarity score
        jaccard_score = len(intersection) / len(union) if union else 0.0
        
        if jaccard_score > 0:
            scored_services.append((other, jaccard_score))
            
    # Sort services by similarity score (descending)
    scored_services.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N services
    return [item[0] for item in scored_services[:limit]]
