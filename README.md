## Sigfox Integration for Home Assistant

This is a custom component for Home Assistant that provides integration with the Sigfox Cloud API V2. It allows you to monitor your Sigfox devices directly from Home Assistant.

### Why was this created?

The built-in Sigfox component in Home Assistant is no longer functional because it uses the deprecated Sigfox Cloud API V1, which was discontinued on March 31, 2020. Since the built-in component is unmaintained, this custom component was developed to provide a working integration using the Sigfox Cloud API V2.

Note: Due to Home Assistant's development policies, this custom component cannot be submitted as an official integration because it includes the API interaction code directly within the component. According to Home Assistant's guidelines, integrations should rely on standalone Python libraries for API interactions.

### Features

- Fetch device information from the Sigfox Cloud.
- Monitor device status, communication state, and link quality.
- Receive the latest messages from your Sigfox devices.
- Supports multiple devices associated with your Sigfox account.

### Install

Add this repo as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/):
It should then appear as a new integration. Click on it. If necessary, search for "sigfox".
```text
https://github.com/mochipon/homeassistant-sigfox
```

Or use this button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mochipon&repository=homeassistant-sigfox&category=integration)
