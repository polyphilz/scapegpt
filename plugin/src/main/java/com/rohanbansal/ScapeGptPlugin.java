package com.rohanbansal;

import com.google.inject.Provides;
import java.awt.image.BufferedImage;
import javax.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import net.runelite.api.ChatMessageType;
import net.runelite.api.Client;
import net.runelite.api.GameState;
import net.runelite.api.events.GameStateChanged;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.eventbus.Subscribe;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.ui.ClientToolbar;
import net.runelite.client.ui.NavigationButton;
import net.runelite.client.util.ImageUtil;

@Slf4j
@PluginDescriptor(
	name = "ScapeGPT",
	loadWhenOutdated = true
)
public class ScapeGptPlugin extends Plugin
{
	@Inject
	private ClientToolbar clientToolbar;

//	@Inject
//	private Client client;

	@Inject
	private ScapeGptConfig config;

	private ScapeGptPanel panel;
	private NavigationButton navButton;

	@Override
	protected void startUp() throws Exception
	{
		log.info("ScapeGPT started!");

		panel = injector.getInstance(ScapeGptPanel.class);
//		panel.init(config);
		panel.init();

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
	protected void shutDown() throws Exception
	{
		log.info("ScapeGPT stopped!");
		clientToolbar.removeNavigation(navButton);
	}

	@Subscribe
	public void onGameStateChanged(GameStateChanged gameStateChanged)
	{
//		if (gameStateChanged.getGameState() == GameState.LOGGED_IN)
//		{
//			client.addChatMessage(ChatMessageType.GAMEMESSAGE, "", "ScapeGPT says " + config.greeting(), null);
//		}
	}

	@Provides
	ScapeGptConfig provideConfig(ConfigManager configManager)
	{
		return configManager.getConfig(ScapeGptConfig.class);
	}
}
