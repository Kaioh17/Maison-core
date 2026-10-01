## Booking lifecycle
A booking moves pending, then confirmed, then completed. It can also be cancelled or delayed.
The price is calculated when the rider books, from Mapbox route distance and time plus your pricing settings.
A deposit is charged at booking creation and the balance is charged at completion, with the driver paid out through Stripe Connect.
Zelle and cash are supported as manual payment methods when enabled in Booking Settings.

## Drivers
Drivers are either in-house or outsourced (subcontractors). Invite a driver from the Drivers page; they receive an onboarding link, apply, and appear as unapproved until you approve them.
A driver must be active and approved to be assigned rides. Drivers connect a Stripe Express account to receive payouts.
Assign a driver to a vehicle from the Drivers or Vehicles page, and to a booking from the Bookings page.

## Vehicles and pricing
Add vehicles under Vehicles. Each vehicle belongs to a vehicle class (category) with its own rates, configured under Settings, Vehicle Classes and Pricing.
Riders only see vehicles that exist and are available. Vehicle images can be hidden from riders in Booking Settings.

## Riders and your white-label site
Riders sign up and book on your own subdomain (yourslug.domain). Branding controls what they see. Riders can install the site as a PWA on their phone, and the manifest and icons use your branding.
Reminder emails go out automatically before a ride, and confirmation emails when a booking is made.
