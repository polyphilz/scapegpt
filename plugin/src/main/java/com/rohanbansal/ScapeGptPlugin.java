package com.rohanbansal;

import com.google.gson.Gson;
import com.google.inject.Provides;
import java.awt.image.BufferedImage;
import javax.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.client.account.AccountSession;
import net.runelite.client.account.SessionManager;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.ui.ClientToolbar;
import net.runelite.client.ui.NavigationButton;
import net.runelite.client.util.ImageUtil;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;

@Slf4j
@PluginDescriptor(
	name = "ScapeGPT",
	loadWhenOutdated = true
)
public class ScapeGptPlugin extends Plugin
{
	@Inject
	private ClientToolbar clientToolbar;

	@Inject
	private ScapeGptConfig config;

	@Inject
	private SessionManager sessionManager;

	private ScapeGptClient scapeGptClient;
	private ScapeGptPanel panel;
	private NavigationButton navButton;
	private HttpUrl apiUrl;

	@Override
	protected void startUp() {
//		apiUrl = new HttpUrl.Builder().scheme("http").host("3.238.6.223").port(8080).build();
		apiUrl = new HttpUrl.Builder().scheme("http").host("44.211.86.102").build();

		AccountSession accountSession = sessionManager.getAccountSession();
		System.out.println(accountSession.getUuid());

		scapeGptClient = new ScapeGptClient(new OkHttpClient(), apiUrl, new Gson());
        if (accountSession != null) {
            scapeGptClient.setUuid(accountSession.getUuid());
        } else {
            scapeGptClient.setUuid(null);
        }

		panel = injector.getInstance(ScapeGptPanel.class);
		panel.init(scapeGptClient);

		final BufferedImage icon = ImageUtil.loadImageResource(getClass(), "scapegpt-icon.png");

		navButton = NavigationButton.builder()
				.tooltip("ScapeGPT")
				.icon(icon)
				.priority(13)
				.panel(panel)
				.build();

		clientToolbar.addNavigation(navButton);
	}

	@Override
	protected void shutDown() {
		clientToolbar.removeNavigation(navButton);
	}

	@Provides
	ScapeGptConfig provideConfig(ConfigManager configManager)
	{
		return configManager.getConfig(ScapeGptConfig.class);
	}
}
