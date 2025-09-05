#!/usr/bin/env python3
"""
Use Playwright to observe the Secrets Manager GUI, log in, and capture screenshots.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time

async def observe_secrets_manager():
    """Observe the Secrets Manager GUI and capture screenshots."""
    
    print("=" * 60)
    print("🔍 Observing Secrets Manager GUI with Playwright")
    print("=" * 60)
    
    # Create screenshots directory
    screenshots_dir = "/home/murr2k/projects/thingy91/secrets_gui/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser (headless mode)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        print("\n📱 Browser launched")
        
        try:
            # Step 1: Navigate to the login page
            print("\n1️⃣ Navigating to http://localhost:5000...")
            await page.goto('http://localhost:5000', wait_until='networkidle')
            
            # Take screenshot of login page
            login_screenshot = f"{screenshots_dir}/01_login_page.png"
            await page.screenshot(path=login_screenshot, full_page=True)
            print(f"   ✅ Screenshot saved: {login_screenshot}")
            
            # Check if we're on the login page
            title = await page.title()
            print(f"   Page title: {title}")
            
            # Step 2: Fill in login credentials
            print("\n2️⃣ Logging in with admin/changeme...")
            
            # Look for username and password fields
            username_input = page.locator('input[name="username"], input[type="text"], #username')
            password_input = page.locator('input[name="password"], input[type="password"], #password')
            
            # Fill credentials
            await username_input.fill('admin')
            await password_input.fill('changeme')
            
            # Find and click login button
            login_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in")')
            await login_button.click()
            
            # Wait for navigation after login
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # Give extra time for any animations
            
            # Step 3: Capture dashboard
            print("\n3️⃣ Capturing dashboard...")
            dashboard_screenshot = f"{screenshots_dir}/02_dashboard.png"
            await page.screenshot(path=dashboard_screenshot, full_page=True)
            print(f"   ✅ Screenshot saved: {dashboard_screenshot}")
            
            # Get current URL to verify we're logged in
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # Step 4: Check for service status indicators
            print("\n4️⃣ Checking service status indicators...")
            
            # Look for service cards or status indicators
            service_cards = page.locator('.service-card, .card, [class*="service"]')
            service_count = await service_cards.count()
            print(f"   Found {service_count} service cards")
            
            # Look specifically for Fly.io service
            flyio_elements = page.locator('*:has-text("Fly.io"), *:has-text("flyio")')
            flyio_count = await flyio_elements.count()
            if flyio_count > 0:
                print(f"   ✅ Found Fly.io service element")
                
                # Try to find status indicators
                status_indicators = page.locator('.status-indicator, .badge, [class*="status"], [class*="health"]')
                status_count = await status_indicators.count()
                print(f"   Found {status_count} status indicators")
                
                # Look for green/healthy status
                healthy_indicators = page.locator('[class*="success"], [class*="healthy"], [class*="green"], .text-success, .bg-success')
                healthy_count = await healthy_indicators.count()
                if healthy_count > 0:
                    print(f"   ✅ Found {healthy_count} healthy status indicators")
            else:
                print("   ⚠️  Fly.io service not visible on page")
            
            # Step 5: Try to interact with services
            print("\n5️⃣ Attempting to view service details...")
            
            # Click on a service card if available
            if service_count > 0:
                first_service = service_cards.first
                await first_service.click()
                await asyncio.sleep(1)
                
                detail_screenshot = f"{screenshots_dir}/03_service_detail.png"
                await page.screenshot(path=detail_screenshot, full_page=True)
                print(f"   ✅ Screenshot saved: {detail_screenshot}")
            
            # Step 6: Extract visible text for analysis
            print("\n6️⃣ Extracting page content...")
            
            # Get all visible text
            page_text = await page.inner_text('body')
            
            # Save page content
            content_file = f"{screenshots_dir}/page_content.txt"
            with open(content_file, 'w') as f:
                f.write(f"Page URL: {current_url}\n")
                f.write(f"Page Title: {title}\n")
                f.write("-" * 40 + "\n")
                f.write(page_text)
            print(f"   ✅ Page content saved: {content_file}")
            
            # Look for specific status text
            if 'healthy' in page_text.lower() or 'connected' in page_text.lower() or '✅' in page_text:
                print("   ✅ Found healthy status indicators in page text")
            
            if 'fly.io' in page_text.lower() or 'flyio' in page_text.lower():
                print("   ✅ Fly.io service is visible on the page")
            
            # Step 7: Check console for any errors
            console_messages = []
            page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
            
            # Reload to capture console messages
            await page.reload()
            await asyncio.sleep(2)
            
            if console_messages:
                print("\n7️⃣ Console messages:")
                for msg in console_messages[:5]:  # Show first 5 messages
                    print(f"   {msg}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            # Take error screenshot
            error_screenshot = f"{screenshots_dir}/error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_screenshot, full_page=True)
            print(f"   Error screenshot saved: {error_screenshot}")
        
        finally:
            await browser.close()
    
    print("\n" + "=" * 60)
    print("✅ GUI observation complete!")
    print(f"\n📸 Screenshots saved in: {screenshots_dir}")
    print("   - 01_login_page.png: Login page")
    print("   - 02_dashboard.png: Main dashboard after login")
    print("   - 03_service_detail.png: Service detail view (if available)")
    print("   - page_content.txt: Extracted page text")
    print("=" * 60)

async def main():
    """Main entry point."""
    await observe_secrets_manager()

if __name__ == "__main__":
    asyncio.run(main())